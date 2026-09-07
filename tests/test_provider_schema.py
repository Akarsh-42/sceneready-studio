"""Regression coverage for Gemini schema complexity without weakening validation."""
import unittest

from pydantic import ValidationError

from app.providers import gemini_output_schema
from app.schemas import Assessment, Breakdown
from test_validation import assessment, breakdown


class ProviderSchemaTests(unittest.TestCase):
    def test_schema_preserves_fields_types_enums_and_references(self):
        def compare(original, wire):
            if isinstance(original, list):
                self.assertEqual(len(original), len(wire))
                for left, right in zip(original, wire):
                    compare(left, right)
            elif isinstance(original, dict):
                omitted = {"minLength", "maxLength", "minItems", "maxItems", "title"}
                self.assertEqual(set(wire), set(original) - omitted)
                for key in wire:
                    if key in {"properties", "$defs"}:
                        self.assertEqual(set(original[key]), set(wire[key]))
                        for name in original[key]:
                            compare(original[key][name], wire[key][name])
                    else:
                        compare(original[key], wire[key])
            else:
                self.assertEqual(original, wire)

        for model in (Breakdown, Assessment):
            with self.subTest(model=model.__name__):
                compare(model.model_json_schema(), gemini_output_schema(model).model_json_schema())

    def test_valid_outputs_still_validate(self):
        for model, payload in ((Breakdown, breakdown()), (Assessment, assessment())):
            wrapped = gemini_output_schema(model)
            self.assertEqual(wrapped.model_validate_json(payload.model_dump_json()).model_dump(), payload.model_dump())

    def test_runtime_limits_still_reject_invalid_output(self):
        invalid = []
        data = breakdown().model_dump()
        data["scenes"] *= 9
        invalid.append((Breakdown, data))
        data = breakdown().model_dump()
        data["summary"] = "x" * 801
        invalid.append((Breakdown, data))
        data = assessment().model_dump()
        data["tasks"][0]["citations"][0]["quote"] = "short"
        invalid.append((Assessment, data))
        data = assessment().model_dump()
        data["tasks"][0]["priority"] = "invented"
        invalid.append((Assessment, data))
        for model, payload in invalid:
            with self.subTest(model=model.__name__):
                with self.assertRaises(ValidationError):
                    gemini_output_schema(model).model_validate(payload)


if __name__ == "__main__":
    unittest.main()
