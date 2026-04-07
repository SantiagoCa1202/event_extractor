import unittest

from beo_pipeline.menu_extractor import extract_menu_sections


class MenuExtractorTests(unittest.TestCase):
    def test_extracts_display_and_subitems(self) -> None:
        raw = "\n".join(
            [
                "2:30 PM Break LM PDR",
                "Nacho Display",
                "Tortilla Chips, Ground Beef, Nacho Cheese",
                "Pickled Jalapenos",
                "Tomatoes",
                "Green Onion",
            ]
        )
        sections = extract_menu_sections(raw)
        self.assertEqual(sections[0].title, "Nacho Display")
        self.assertGreaterEqual(len(sections[0].items), 5)

    def test_extracts_plated_courses(self) -> None:
        raw = "\n".join(
            [
                "12:00 PM Plated Lunch Carolina Ballroom",
                "Hot Plated Lunch",
                "Mixed Greens- Cucumber, Radish, Tomatoes",
                "Roasted Airline Chicken Breast with Herb Roasted Potatoes",
                "Chef's Choice Dessert- Two Types at Alternative Place Settings",
            ]
        )
        sections = extract_menu_sections(raw)
        titles = [section.title for section in sections]
        self.assertIn("Mixed Greens", titles)
        self.assertIn("Chef's Choice Dessert", titles)


if __name__ == "__main__":
    unittest.main()
