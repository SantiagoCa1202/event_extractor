import unittest

from beo_pipeline.menu_extractor import derive_menu_style, extract_menu_sections


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
                "Mixed Greens- Cucumber, Radish, Tomatoes, Carrots, Ranch and Balsamic Vinaigrette on Table",
                "Rolls with Butter",
                "Roasted Airline Chicken Breast with Herb Roasted Potatoes",
                "Chef's Choice Dessert- Two Types at Alternative Place Settings",
            ]
        )
        sections = extract_menu_sections(raw)
        titles = [section.title for section in sections]
        self.assertIn("Mixed Greens", titles)
        self.assertIn("Chef's Choice Dessert", titles)
        salad_section = next(section for section in sections if section.title == "Mixed Greens")
        self.assertEqual(salad_section.course_type, "salad")
        salad_names = [item.name for item in salad_section.items]
        self.assertEqual(
            salad_names,
            ["Cucumber", "Radish", "Tomatoes", "Carrots", "Ranch", "Balsamic Vinaigrette"],
        )
        item_section = next(section for section in sections if section.title == "Items")
        self.assertIn("Rolls with Butter", [item.name for item in item_section.items])
        dessert_section = next(section for section in sections if section.title == "Chef's Choice Dessert")
        self.assertEqual(dessert_section.course_type, "dessert")
        self.assertEqual(
            [item.name for item in dessert_section.items],
            ["Two Types at Alternative Place Settings"],
        )

    def test_extracts_inline_mixed_green_salad_for_plated(self) -> None:
        raw = "\n".join(
            [
                "12:00 PM Plated Lunch Carolina Ballroom",
                "Mixed Green Salad, Cucumbers, Carrots, Tomatoes, Radish Ranch and Balsamic Vinaigrette on Tables",
            ]
        )
        sections = extract_menu_sections(raw)
        salad_section = next(section for section in sections if section.title == "Mixed Green Salad")
        self.assertEqual(salad_section.course_type, "salad")
        self.assertEqual(
            [item.name for item in salad_section.items],
            ["Cucumbers", "Carrots", "Tomatoes", "Radish", "Ranch", "Balsamic Vinaigrette"],
        )

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
        self.assertEqual(len(sections), 1)
        self.assertEqual(sections[0].title, "")
        self.assertEqual(sections[0].type, "snack_items")
        snack_names = [item.name for item in sections[0].items]
        self.assertIn("Assorted Full-Size Candy Bars", snack_names)
        self.assertIn("Assorted Protein Bars", snack_names)

    def test_food_bar_is_station_not_beverage(self) -> None:
        raw = "\n".join(
            [
                "5:30 PM Reception CJs",
                "Mac n' Cheese Bar",
                "Grilled Chicken, Brisket Burnt Ends, Bacon Lardons",
            ]
        )
        sections = extract_menu_sections(raw)
        self.assertEqual(sections[0].title, "Mac n' Cheese Bar")
        self.assertEqual(sections[0].type, "station_items")
        self.assertEqual(sections[0].service_role, "station")
        self.assertEqual(sections[0].course_type, "other")

    def test_filters_repeated_page_header_noise(self) -> None:
        raw = "\n".join(
            [
                "5:30 PM Reception CJs",
                "Premium Bar Host",
                "Tito's Vodka",
                "EVENT ORDER Page # 2 of 2",
                "SHERATON CHARLOTTE HOTEL Event Order #: 708368",
                "555 South McDowell Street, South Tower, Charlotte, NC 28204 Quote #: M-V0AVZDD",
                "PHONE:(704) 372-4100 Folio #: 1233367",
                "FUNCTION DAY/DATE: Tuesday, April 07, 2026",
                "ORGANIZATION: Maximo Utility Working Group",
                "Makers Mark Kentucky Bourbon",
                "(group is mostly beer drinkers)",
            ]
        )
        sections = extract_menu_sections(raw)
        names = [item.name for section in sections for item in section.items]
        self.assertIn("Tito's Vodka", names)
        self.assertIn("Makers Mark Kentucky Bourbon", names)
        self.assertNotIn("EVENT ORDER Page # 2 of 2", names)
        self.assertNotIn("SHERATON CHARLOTTE HOTEL Event Order #: 708368", names)
        self.assertNotIn("PHONE:(704) 372-4100 Folio #: 1233367", names)
        self.assertNotIn("ORGANIZATION: Maximo Utility Working Group", names)

    def test_breakfast_sandwich_variants_stay_whole_and_absorb_quantity_line(self) -> None:
        raw = "\n".join(
            [
                "7:00 AM Continental Breakfast Symphony Convention Foyer",
                "(200) Breakfast Sandwiches @ $11.7 Each",
                "Croissant Sandwich - Smoked Ham, Egg Patty, American Cheese",
                "Biscuit Sandwich - Smoked Bacon, Egg Patty, American Cheese",
                "Bagel Sandwich - Pork Sage Sausage, Egg Patty, Cheddar Cheese",
                "English Muffin - Turkey Sausage, Egg Patty, American Cheese",
                "50 each",
            ]
        )
        sections = extract_menu_sections(raw)
        target = sections[0]
        self.assertEqual(target.title, "Items")
        names = [item.name for item in target.items]
        self.assertIn("Croissant Sandwich - Smoked Ham, Egg Patty, American Cheese", names)
        self.assertIn("Biscuit Sandwich - Smoked Bacon, Egg Patty, American Cheese", names)
        self.assertIn("Bagel Sandwich - Pork Sage Sausage, Egg Patty, Cheddar Cheese", names)
        self.assertIn("English Muffin - Turkey Sausage, Egg Patty, American Cheese", names)
        self.assertNotIn("50 each", names)
        for item in target.items:
            self.assertEqual(item.quantity, 50)
            self.assertEqual(item.unit, "each")

    def test_omits_non_area_coffee_service_items(self) -> None:
        raw = "\n".join(
            [
                "10:00 AM Coffee Break Symphony Convention Foyer",
                "Assorted Pepsi Sodas",
                "Freshly Brewed Starbucks Regular and Decaffeinated Coffee to Include Sweeteners, Dairy & Non Dairy Add-Ins",
                "Bottled Water",
                "Assorted Tazo Teas and Condiments",
                "Tractor Iced Tea & Starbucks Coffee",
                "(Heavy Regular Coffee)",
                "(25) Lemon Bars @ $50.4 per Dozen",
            ]
        )
        sections = extract_menu_sections(raw)
        names = [item.name for section in sections for item in section.items]
        self.assertNotIn("Assorted Pepsi Sodas", names)
        self.assertNotIn("Freshly Brewed Starbucks Regular and Decaffeinated Coffee to Include Sweeteners", names)
        self.assertNotIn("Bottled Water", names)
        self.assertNotIn("Assorted Tazo Teas and Condiments", names)
        self.assertNotIn("Dairy", names)
        self.assertNotIn("Tractor Iced Tea", names)
        self.assertNotIn("Starbucks Coffee", names)
        self.assertNotIn(
            "Tractor Iced Tea & Starbucks Coffee (Preset Water-- Coffee and Ice Tea Offered Tableside)",
            names,
        )

    def test_omits_assorted_cereals_from_continental(self) -> None:
        raw = "\n".join(
            [
                "7:00 AM Continental Breakfast Symphony Convention Foyer",
                "Continental",
                "Danish, Croissants, Mini Biscuits",
                "Strawberry + Apricot Jam",
                "Assorted Cereals",
                "Individual Yogurts",
                "Fresh Sliced Fruit",
                "Starbucks Regular & Decaf Coffee",
                "Tea, Orange Juice",
            ]
        )
        sections = extract_menu_sections(raw)
        names = [item.name for section in sections for item in section.items]
        self.assertNotIn("Assorted Cereals", names)
        self.assertNotIn("Starbucks Regular", names)
        self.assertNotIn("Decaf Coffee", names)
        self.assertNotIn("Tea", names)
        self.assertNotIn("Orange Juice", names)
        self.assertIn("Individual Yogurts", names)
        self.assertIn("Fresh Sliced Fruit", names)

    def test_priced_food_item_stays_as_item_not_section_title(self) -> None:
        raw = "\n".join(
            [
                "2:15 PM Coffee Break Symphony Convention Foyer",
                "Starbucks Regular and Decaffeinated Coffee, Assorted Tazo Teas and Condiments @ $94.5 per Gallon",
                "To Include Sweeteners, Dairy & Non Dairy Add-Ins",
                "(25) Lemon Bars @ $50.4 per Dozen",
                "Tractor Organic Artisan Unsweetened Iced Tea, Seasonal Fruit Beverage @ $81 per Gallon",
            ]
        )
        sections = extract_menu_sections(raw)
        self.assertEqual(len(sections), 1)
        self.assertEqual(sections[0].title, "Items")
        self.assertEqual(len(sections[0].items), 1)
        item = sections[0].items[0]
        self.assertEqual(item.name, "Lemon Bars")
        self.assertEqual(item.quantity, 25)
        self.assertEqual(item.unit, "dozen")

    def test_ignores_pending_chefs_choice_placeholder(self) -> None:
        raw = "\n".join(
            [
                "7:00 AM Continental Breakfast Symphony Convention Foyer",
                "Continental",
                "(200) Breakfast Burritos @ $11.7 Each",
                "Chef's Choice- Assorted Variety",
            ]
        )
        sections = extract_menu_sections(raw)
        names = [item.name for section in sections for item in section.items]
        titles = [section.title for section in sections]
        self.assertIn("Breakfast Burritos", names)
        self.assertNotIn("Chef's Choice- Assorted Variety", names)
        self.assertNotIn("Chef's Choice", titles)

    def test_splits_steel_cut_oatmeal_from_cold_toppings(self) -> None:
        raw = "\n".join(
            [
                "7:00 AM Continental Breakfast Symphony Convention Foyer",
                "Steel Cut Oatmeal with Golden Raises, Sliced Almonds & Brown Sugar",
            ]
        )
        sections = extract_menu_sections(raw)
        names = [item.name for section in sections for item in section.items]
        self.assertEqual(
            names,
            ["Steel Cut Oatmeal", "Golden Raises", "Sliced Almonds", "Brown Sugar"],
        )

    def test_greens_and_toppings_becomes_section_and_rejoins_white_balsamic(self) -> None:
        raw = "\n".join(
            [
                "12:00 PM Lunch Buffet",
                "Greens & Toppings: Spring Mix With Cherry Tomato, Cucumber, Shredded Carrot, Shredded Cheddar, Black Olives, Buttermilk Ranch, White",
                "Balsamic Dressing",
            ]
        )
        sections = extract_menu_sections(raw)
        self.assertEqual(len(sections), 1)
        section = sections[0]
        self.assertEqual(section.title, "Greens & Toppings")
        self.assertEqual(section.type, "cold_items")
        names = [item.name for item in section.items]
        self.assertIn("Spring Mix With Cherry Tomato", names)
        self.assertIn("Cucumber", names)
        self.assertIn("Shredded Carrot", names)
        self.assertIn("Shredded Cheddar", names)
        self.assertIn("Black Olives", names)
        self.assertIn("Buttermilk Ranch", names)
        self.assertIn("White Balsamic Dressing", names)

    def test_menu_style_title_does_not_absorb_real_subsections(self) -> None:
        raw = "\n".join(
            [
                "12:00 PM Lunch Buffet",
                "The Queens Table",
                "Assorted Rolls with Butter",
                "Greens & Toppings: Spring Mix With Cherry Tomato, Cucumber, Shredded Carrot, Shredded Cheddar, Black Olives, Buttermilk Ranch, White",
                "Balsamic Dressing",
                "Choice of Two Proteins:",
                "Roasted Lemon Thyme Chicken Breast",
                "Sides: Garlic Mashed Potatoes & Sauteed Green Beans",
                "Dessert: Assorted Sliced Cake",
            ]
        )
        sections = extract_menu_sections(raw)
        titles = [section.title for section in sections]
        self.assertNotIn("The Queens Table", titles)
        self.assertIn("Greens & Toppings", titles)
        self.assertIn("Choice of Two Proteins:", titles)
        self.assertIn("Sides", titles)
        self.assertIn("Dessert", titles)
        self.assertEqual(derive_menu_style(raw, sections), "The Queens Table")
        item_section = next(section for section in sections if section.title == "Items")
        item_names = [item.name for item in item_section.items]
        self.assertIn("Assorted Rolls with Butter", item_names)

    def test_special_plate_counts_become_notes_not_items(self) -> None:
        raw = "\n".join(
            [
                "12:00 PM Plated Lunch Carolina Ballroom",
                "Roasted Airline Chicken Breast with Herb Roasted Potatoes, Broccolini, and Lemon Thyme Jus",
                "(20) vegan/vegeterian",
            ]
        )
        sections = extract_menu_sections(raw)
        item_section = next(section for section in sections if section.title == "Items")
        self.assertEqual(len(item_section.items), 1)
        self.assertEqual(
            item_section.items[0].name,
            "Roasted Airline Chicken Breast with Herb Roasted Potatoes, Broccolini, and Lemon Thyme Jus",
        )
        self.assertEqual(item_section.items[0].notes, "(20) vegan/vegeterian")

    def test_keeps_undetailed_displays_and_stations_as_empty_sections(self) -> None:
        raw = "\n".join(
            [
                "5:00 PM Reception Carolina Ballroom",
                "Cheese Display",
                "Vegetable Display",
                "Charcuterie Display",
                "Pepper Crusted Tenderloin Carving Station",
                "Turkey Breast Carving Station",
                "Cedar Plank Salmon Carving Station",
                "Mashed Potato Bar",
            ]
        )
        sections = extract_menu_sections(raw)
        self.assertEqual(
            [section.title for section in sections],
            [
                "Cheese Display",
                "Vegetable Display",
                "Charcuterie Display",
                "Pepper Crusted Tenderloin Carving Station",
                "Turkey Breast Carving Station",
                "Cedar Plank Salmon Carving Station",
                "Mashed Potato Bar",
            ],
        )
        self.assertEqual(
            [section.type for section in sections],
            ["display", "display", "display", "station_items", "station_items", "station_items", "station_items"],
        )
        self.assertTrue(all(not section.items for section in sections))


if __name__ == "__main__":
    unittest.main()
