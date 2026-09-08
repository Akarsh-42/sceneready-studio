import json
import os
import unittest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from pydantic import ValidationError
from app.main import app
from app.storyboard import Shot, ShotPlan, StoryboardRequest, generate_storyboard

SCENE = dict(id='S01', heading='INT. STATION - NIGHT', setting='interior',
             time_of_day='night', people=['Adult courier'], equipment=[],
             production_needs=[], script_excerpt='An adult courier enters the empty station.')


def plan(n=3):
    return ShotPlan(continuity='Courier in red coat. Blue-lit station.', assumptions=['Red coat'],
                    shots=[Shot(shot_type='Wide' if i == 0 else 'Close-up', camera='Eye level',
                                description=f'Beat {i}', image_prompt=f'Frame {i}') for i in range(n)])


class StoryboardTests(unittest.IsolatedAsyncioTestCase):
    async def test_planning_precedes_images_and_reference_reused(self):
        provider = AsyncMock()
        provider.plan.return_value = plan()
        provider.image.side_effect = [(b'first','image/png'),(b'second','image/png'),(b'third','image/png')]
        events = [e async for e in generate_storyboard(StoryboardRequest(scene=SCENE), provider)]
        self.assertEqual(events[1]['type'], 'plan')
        self.assertEqual(provider.image.call_args_list[0].args[2], None)
        self.assertEqual(provider.image.call_args_list[1].args[2], (b'first','image/png'))
        self.assertEqual(provider.image.call_args_list[2].args[2], (b'first','image/png'))
        self.assertEqual(events[-1]['successful'], 3)

    async def test_partial_failure_preserves_plan_and_frames(self):
        provider=AsyncMock();provider.plan.return_value=plan()
        provider.image.side_effect=[ValueError('blocked'),(b'ok','image/png'),ValueError('unavailable')]
        events=[e async for e in generate_storyboard(StoryboardRequest(scene=SCENE),provider)]
        self.assertEqual(sum(e['type']=='frame_error' for e in events),2)
        self.assertEqual(events[-1]['successful'],1)
        self.assertEqual(provider.image.call_args_list[2].args[2],(b'ok','image/png'))

    async def test_bad_plan_makes_no_image_calls(self):
        provider=AsyncMock();provider.plan.return_value=plan(2)
        with self.assertRaises(ValueError):
            _=[e async for e in generate_storyboard(StoryboardRequest(scene=SCENE),provider)]
        provider.image.assert_not_called()

    def test_bounds(self):
        for n in (1,5):
            with self.assertRaises(ValidationError):StoryboardRequest(scene=SCENE,shot_count=n)


class StoryboardApiTests(unittest.TestCase):
    def test_auth_limits_demo_and_live(self):
        with patch.dict(os.environ,{'STUDIO_ACCESS_TOKEN':'x'*24,'SCENEREADY_DEMO':'1','GOOGLE_CLOUD_PROJECT':'test'}), TestClient(app) as client:
            headers={'Authorization':'Bearer '+'x'*24}
            self.assertEqual(client.post('/api/storyboard',json={'scene':SCENE}).status_code,401)
            self.assertEqual(client.post('/api/storyboard',content=b'x'*65537,headers=headers).status_code,413)
            self.assertEqual(client.post('/api/storyboard',json={'scene':SCENE},headers=headers).status_code,503)
            with patch.dict(os.environ,{'SCENEREADY_DEMO':'0'}):
                self.assertEqual(client.post('/api/storyboard',json={'scene':SCENE,'shot_count':5},headers=headers).status_code,422)
                with patch('app.storyboard.StoryboardProvider.plan',new=AsyncMock(return_value=plan())), patch('app.storyboard.StoryboardProvider.image',new=AsyncMock(return_value=(b'image','image/png'))):
                    result=client.post('/api/storyboard',json={'scene':SCENE},headers=headers)
                    events=[json.loads(line) for line in result.text.splitlines()]
                    self.assertEqual(events[-1]['successful'],3)
                    self.assertEqual(result.headers['cache-control'],'no-store')
