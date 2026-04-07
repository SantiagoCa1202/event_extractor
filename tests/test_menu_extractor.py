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

    def test_break_groups_snacks_without_breaking_hyphenated_names(self) -> None:
        raw = "\n".join(
            [
                "12:00 PM Meeting Executive Boardroom",
                "Half Day Beverage Break",
                "Assorted Pepsi Sodas",
                "Freshly Brewed Starbucks Regular and Decaffeinated Coffee to Include Sweeteners, Dairy & Non Dairy Add-Ins",
                "Assorted Teavana Teas",
                "Bottled Water",
                "Half Day Break Based On 4 Hours",
                "$38.00 per Person",
                "Assorted Granola Bars @ $5 Each",
                "Charged on Consumption",
                "Assorted Miss Vicky Kettle Chips @ $5 Each",
                "Charged on Consumption",
                "Assorted Full-Size Candy Bars @ $5 Each",
                "Charged on Consumption",
                "Assorted Protein Bars @ $7 Each",
                "Charged on Consumption",
            ]
        )
        sections = extract_menu_sections(raw)
        self.assertEqual(len(sections), 2)
        self.assertEqual(sections[0].title, "Half Day Beverage Break")
        self.assertEqual(sections[0].type, "break_items")
        self.assertEqual(sections[1].title, "")
        self.assertEqual(sections[1].type, "snack_items")
        snack_names = [item.name for item in sections[1].items]
        self.assertIn("Assorted Full-Size Candy Bars", snack_names)
        self.assertIn("Assorted Protein Bars", snack_names)


if __name__ == "__main__":
    unittest.main()
