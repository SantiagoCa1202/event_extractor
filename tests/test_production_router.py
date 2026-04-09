import unittest

from beo_pipeline.production_router import annotate_menu_sections_with_production


class ProductionRouterTests(unittest.TestCase):
    def test_routes_nacho_display_items(self) -> None:
        sections = [
            {
                "title": "Nacho Display",
                "type": "display",
                "service_role": "display",
                "course_type": "other",
                "items": [
                    {"name": "Tortilla Chips", "source_text": "Tortilla Chips, Ground Beef, Nacho Cheese"},
                    {"name": "Ground Beef", "source_text": "Tortilla Chips, Ground Beef, Nacho Cheese"},
                    {"name": "Nacho Cheese", "source_text": "Tortilla Chips, Ground Beef, Nacho Cheese"},
                    {"name": "Pickled Jalapenos", "source_text": "Pickled Jalapenos"},
                    {"name": "Tomatoes", "source_text": "Tomatoes"},
                    {"name": "Green Onion", "source_text": "Green Onion"},
                    {"name": "Sour Cream", "source_text": "Sour Cream"},
                    {"name": "Corn Relish", "source_text": "Corn Relish"},
                ],
            }
        ]
        annotated = annotate_menu_sections_with_production(sections)
        items = {item["name"]: item["production_area"]["temperature_zone"] for item in annotated[0]["items"]}
        self.assertEqual(items["Ground Beef"], "hot_kitchen")
        self.assertEqual(items["Nacho Cheese"], "hot_kitchen")
        self.assertEqual(items["Pickled Jalapenos"], "cold_kitchen")
        self.assertEqual(items["Tomatoes"], "cold_kitchen")
        self.assertEqual(items["Sour Cream"], "cold_kitchen")
        self.assertEqual(annotated[0]["operational_split"]["unknown_items"], [])

    def test_routes_break_beverages_and_snacks(self) -> None:
        sections = [
            {
                "title": "Half Day Beverage Break",
                "type": "break_items",
                "service_role": "break",
                "course_type": "beverage",
                "items": [
                    {"name": "Assorted Pepsi Sodas", "source_text": "Assorted Pepsi Sodas"},
                    {"name": "Assorted Teavana Teas", "source_text": "Assorted Teavana Teas"},
                    {"name": "Bottled Water", "source_text": "Bottled Water"},
                ],
            },
            {
                "title": "",
                "type": "snack_items",
                "service_role": "bar",
                "course_type": "break",
                "items": [
                    {"name": "Assorted Granola Bars", "source_text": "Assorted Granola Bars @ $5 Each"},
                    {"name": "Assorted Protein Bars", "source_text": "Assorted Protein Bars @ $7 Each"},
                ],
            },
        ]
        annotated = annotate_menu_sections_with_production(sections)
        beverages = {item["name"]: item["production_area"]["temperature_zone"] for item in annotated[0]["items"]}
        snacks = {item["name"]: item["production_area"]["temperature_zone"] for item in annotated[1]["items"]}
        self.assertEqual(beverages["Assorted Pepsi Sodas"], "unknown")
        self.assertEqual(beverages["Bottled Water"], "unknown")
        self.assertEqual(snacks["Assorted Granola Bars"], "cold_kitchen")
        self.assertEqual(snacks["Assorted Protein Bars"], "cold_kitchen")

    def test_routes_mac_cheese_bar_toppings_to_hot(self) -> None:
        sections = [
            {
                "title": "Mac n' Cheese Bar",
                "type": "station_items",
                "service_role": "station",
                "course_type": "other",
                "items": [
                    {"name": "Grilled Chicken", "source_text": "Grilled Chicken, Brisket Burnt Ends, Bacon Lardons"},
                    {"name": "Brisket Burnt Ends", "source_text": "Grilled Chicken, Brisket Burnt Ends, Bacon Lardons"},
                    {"name": "Bacon Lardons", "source_text": "Grilled Chicken, Brisket Burnt Ends, Bacon Lardons"},
                    {"name": "Grilled Wild Mushrooms", "source_text": "Grilled Wild Mushrooms, Butter Cracker Crumbs"},
                ],
            }
        ]
        annotated = annotate_menu_sections_with_production(sections)
        items = {item["name"]: item["production_area"]["temperature_zone"] for item in annotated[0]["items"]}
        self.assertEqual(items["Grilled Chicken"], "hot_kitchen")
        self.assertEqual(items["Brisket Burnt Ends"], "hot_kitchen")
        self.assertEqual(items["Bacon Lardons"], "hot_kitchen")
        self.assertEqual(items["Grilled Wild Mushrooms"], "hot_kitchen")

    def test_routes_vegetable_display_to_cold(self) -> None:
        sections = [
            {
                "title": "Vegetable Display",
                "type": "display",
                "service_role": "display",
                "course_type": "other",
                "items": [
                    {"name": "Baby Carrots", "source_text": "Baby Carrots, Celery, Sweet Peppers, Asparagus, Broccolini"},
                    {"name": "Celery", "source_text": "Baby Carrots, Celery, Sweet Peppers, Asparagus, Broccolini"},
                    {"name": "Sweet Peppers", "source_text": "Baby Carrots, Celery, Sweet Peppers, Asparagus, Broccolini"},
                    {"name": "Asparagus", "source_text": "Baby Carrots, Celery, Sweet Peppers, Asparagus, Broccolini"},
                    {"name": "Broccolini", "source_text": "Baby Carrots, Celery, Sweet Peppers, Asparagus, Broccolini"},
                    {"name": "Buttermilk Herb Dip", "source_text": "Buttermilk Herb Dip"},
                ],
            }
        ]
        annotated = annotate_menu_sections_with_production(sections)
        items = {item["name"]: item["production_area"]["temperature_zone"] for item in annotated[0]["items"]}
        self.assertEqual(items["Baby Carrots"], "cold_kitchen")
        self.assertEqual(items["Celery"], "cold_kitchen")
        self.assertEqual(items["Sweet Peppers"], "cold_kitchen")
        self.assertEqual(items["Asparagus"], "cold_kitchen")
        self.assertEqual(items["Broccolini"], "cold_kitchen")
        self.assertEqual(items["Buttermilk Herb Dip"], "cold_kitchen")
        self.assertEqual(annotated[0]["operational_split"]["unknown_items"], [])

    def test_routes_greens_and_toppings_to_cold(self) -> None:
        sections = [
            {
                "title": "Greens & Toppings",
                "type": "cold_items",
                "service_role": "buffet",
                "course_type": "other",
                "items": [
                    {"name": "Spring Mix With Cherry Tomato"},
                    {"name": "Cucumber"},
                    {"name": "Shredded Carrot"},
                    {"name": "Shredded Cheddar"},
                    {"name": "Black Olives"},
                    {"name": "Buttermilk Ranch"},
                    {"name": "White Balsamic Dressing"},
                ],
            }
        ]
        annotated = annotate_menu_sections_with_production(sections)
        items = {item["name"]: item["production_area"]["temperature_zone"] for item in annotated[0]["items"]}
        self.assertEqual(items["Spring Mix With Cherry Tomato"], "cold_kitchen")
        self.assertEqual(items["Cucumber"], "cold_kitchen")
        self.assertEqual(items["Shredded Carrot"], "cold_kitchen")
        self.assertEqual(items["Shredded Cheddar"], "cold_kitchen")
        self.assertEqual(items["Black Olives"], "cold_kitchen")
        self.assertEqual(items["Buttermilk Ranch"], "cold_kitchen")
        self.assertEqual(items["White Balsamic Dressing"], "cold_kitchen")

    def test_routes_cheese_display_to_cold(self) -> None:
        sections = [
            {
                "title": "Cheese Display",
                "type": "display",
                "service_role": "display",
                "course_type": "other",
                "items": [
                    {"name": "Brie", "source_text": "Brie, Gorgonzola, Manchego"},
                    {"name": "Gorgonzola", "source_text": "Brie, Gorgonzola, Manchego"},
                    {"name": "Manchego", "source_text": "Brie, Gorgonzola, Manchego"},
                    {"name": "Grapes", "source_text": "Grapes, Berries, Seasonal Jam"},
                    {"name": "Berries", "source_text": "Grapes, Berries, Seasonal Jam"},
                    {"name": "Seasonal Jam", "source_text": "Grapes, Berries, Seasonal Jam"},
                    {"name": "Assorted Crackers and Toast Points", "source_text": "Assorted Crackers and Toast Points"},
                    {"name": "Dried Apricot", "source_text": "Dried Apricot, Marcona Almonds"},
                    {"name": "Marcona Almonds", "source_text": "Dried Apricot, Marcona Almonds"},
                ],
            }
        ]
        annotated = annotate_menu_sections_with_production(sections)
        items = {item["name"]: item["production_area"]["temperature_zone"] for item in annotated[0]["items"]}
        self.assertEqual(items["Brie"], "cold_kitchen")
        self.assertEqual(items["Gorgonzola"], "cold_kitchen")
        self.assertEqual(items["Manchego"], "cold_kitchen")
        self.assertEqual(items["Grapes"], "cold_kitchen")
        self.assertEqual(items["Seasonal Jam"], "cold_kitchen")
        self.assertEqual(items["Assorted Crackers and Toast Points"], "cold_kitchen")
        self.assertEqual(items["Marcona Almonds"], "cold_kitchen")
        self.assertEqual(annotated[0]["operational_split"]["unknown_items"], [])

    def test_routes_continental_breakfast_to_cold_except_hot_oatmeal(self) -> None:
        sections = [
            {
                "title": "Continental",
                "type": "break_items",
                "service_role": "break",
                "course_type": "other",
                "items": [
                    {"name": "Danish", "source_text": "Danish, Croissants, Mini Biscuits"},
                    {"name": "Croissants", "source_text": "Danish, Croissants, Mini Biscuits"},
                    {"name": "Mini Biscuits", "source_text": "Danish, Croissants, Mini Biscuits"},
                    {"name": "Strawberry", "source_text": "Strawberry + Apricot Jam"},
                    {"name": "Apricot Jam", "source_text": "Strawberry + Apricot Jam"},
                    {"name": "Assorted Cereals", "source_text": "Assorted Cereals"},
                    {"name": "Individual Yogurts", "source_text": "Individual Yogurts"},
                    {"name": "Fresh Sliced Fruit", "source_text": "Fresh Sliced Fruit"},
                    {"name": "Steel Cut Oatmeal", "source_text": "Steel Cut Oatmeal"},
                ],
            }
        ]
        annotated = annotate_menu_sections_with_production(sections)
        items = {item["name"]: item["production_area"]["temperature_zone"] for item in annotated[0]["items"]}
        self.assertEqual(items["Danish"], "cold_kitchen")
        self.assertEqual(items["Croissants"], "cold_kitchen")
        self.assertEqual(items["Mini Biscuits"], "cold_kitchen")
        self.assertEqual(items["Strawberry"], "cold_kitchen")
        self.assertEqual(items["Apricot Jam"], "cold_kitchen")
        self.assertEqual(items["Assorted Cereals"], "cold_kitchen")
        self.assertEqual(items["Individual Yogurts"], "cold_kitchen")
        self.assertEqual(items["Fresh Sliced Fruit"], "cold_kitchen")
        self.assertEqual(items["Steel Cut Oatmeal"], "hot_kitchen")

    def test_routes_breakfast_sandwich_variants_to_hot(self) -> None:
        sections = [
            {
                "title": "(200) Breakfast Sandwiches @ $11.7 Each",
                "type": "break_items",
                "service_role": "break",
                "course_type": "other",
                "items": [
                    {"name": "Croissant Sandwich - Smoked Ham, Egg Patty, American Cheese"},
                    {"name": "Biscuit Sandwich - Smoked Bacon, Egg Patty, American Cheese"},
                    {"name": "Bagel Sandwich - Pork Sage Sausage, Egg Patty, Cheddar Cheese"},
                    {"name": "English Muffin - Turkey Sausage, Egg Patty, American Cheese"},
                ],
            }
        ]
        annotated = annotate_menu_sections_with_production(sections)
        items = {item["name"]: item["production_area"]["temperature_zone"] for item in annotated[0]["items"]}
        self.assertEqual(items["Croissant Sandwich - Smoked Ham, Egg Patty, American Cheese"], "hot_kitchen")
        self.assertEqual(items["Biscuit Sandwich - Smoked Bacon, Egg Patty, American Cheese"], "hot_kitchen")
        self.assertEqual(items["Bagel Sandwich - Pork Sage Sausage, Egg Patty, Cheddar Cheese"], "hot_kitchen")
        self.assertEqual(items["English Muffin - Turkey Sausage, Egg Patty, American Cheese"], "hot_kitchen")

    def test_routes_pastries_and_whole_fruit_to_cold(self) -> None:
        sections = [
            {
                "title": "Items",
                "type": "course",
                "service_role": "other",
                "course_type": "other",
                "items": [
                    {"name": "Assorted Pastries", "source_text": "(15) Assorted Pastries @ $37.8 per Dozen"},
                    {"name": "Assorted Whole Fruit", "source_text": "(15) Assorted Whole Fruit @ $28.8 per Dozen"},
                ],
            }
        ]
        annotated = annotate_menu_sections_with_production(sections)
        items = {item["name"]: item["production_area"]["temperature_zone"] for item in annotated[0]["items"]}
        self.assertEqual(items["Assorted Pastries"], "cold_kitchen")
        self.assertEqual(items["Assorted Whole Fruit"], "cold_kitchen")

    def test_routes_breakfast_burritos_to_hot(self) -> None:
        sections = [
            {
                "title": "Items",
                "type": "course",
                "service_role": "other",
                "course_type": "other",
                "items": [
                    {"name": "Breakfast Burritos", "source_text": "(200) Breakfast Burritos @ $11.7 Each"},
                ],
            }
        ]
        annotated = annotate_menu_sections_with_production(sections)
        item = annotated[0]["items"][0]
        self.assertEqual(item["production_area"]["temperature_zone"], "hot_kitchen")

    def test_routes_breakfast_pastries_jams_cold_and_breakfast_sides_hot(self) -> None:
        sections = [
            {
                "title": "Continental",
                "type": "break_items",
                "service_role": "break",
                "course_type": "other",
                "items": [
                    {"name": "Assorted Danish"},
                    {"name": "Croissants"},
                    {"name": "Biscuits"},
                    {"name": "Strawberry"},
                    {"name": "Apricot Jam"},
                    {"name": "Applewood Smoked Thick Cut Bacon"},
                    {"name": "Rosemary Roasted Potatoes"},
                ],
            }
        ]
        annotated = annotate_menu_sections_with_production(sections)
        items = {item["name"]: item["production_area"]["temperature_zone"] for item in annotated[0]["items"]}
        self.assertEqual(items["Assorted Danish"], "cold_kitchen")
        self.assertEqual(items["Croissants"], "cold_kitchen")
        self.assertEqual(items["Biscuits"], "cold_kitchen")
        self.assertEqual(items["Strawberry"], "cold_kitchen")
        self.assertEqual(items["Apricot Jam"], "cold_kitchen")
        self.assertEqual(items["Applewood Smoked Thick Cut Bacon"], "hot_kitchen")
        self.assertEqual(items["Rosemary Roasted Potatoes"], "hot_kitchen")

    def test_routes_oatmeal_hot_and_toppings_cold(self) -> None:
        sections = [
            {
                "title": "Items",
                "type": "course",
                "service_role": "other",
                "course_type": "other",
                "items": [
                    {"name": "Steel Cut Oatmeal"},
                    {"name": "Golden Raises"},
                    {"name": "Sliced Almonds"},
                    {"name": "Brown Sugar"},
                ],
            }
        ]
        annotated = annotate_menu_sections_with_production(sections)
        items = {item["name"]: item["production_area"]["temperature_zone"] for item in annotated[0]["items"]}
        self.assertEqual(items["Steel Cut Oatmeal"], "hot_kitchen")
        self.assertEqual(items["Golden Raises"], "cold_kitchen")
        self.assertEqual(items["Sliced Almonds"], "cold_kitchen")
        self.assertEqual(items["Brown Sugar"], "cold_kitchen")

    def test_routes_beef_tenderloin_plated_variants_to_hot_by_keyword(self) -> None:
        sections = [
            {
                "title": "Items",
                "type": "course",
                "service_role": "other",
                "course_type": "entree",
                "items": [
                    {"name": "Beef Tenderloin with Mash Potatoes and Sweet Pepper Green Beans, Chimichurri Sauce"},
                    {"name": "Beef Tenderloin with Potato Puree and Asparagus"},
                ],
            }
        ]
        annotated = annotate_menu_sections_with_production(sections)
        items = {item["name"]: item["production_area"] for item in annotated[0]["items"]}
        self.assertEqual(
            items["Beef Tenderloin with Mash Potatoes and Sweet Pepper Green Beans, Chimichurri Sauce"]["temperature_zone"],
            "hot_kitchen",
        )
        self.assertEqual(
            items["Beef Tenderloin with Mash Potatoes and Sweet Pepper Green Beans, Chimichurri Sauce"]["reason"],
            "keyword_item_rule:beef_tenderloin",
        )
        self.assertEqual(items["Beef Tenderloin with Potato Puree and Asparagus"]["temperature_zone"], "hot_kitchen")

    def test_routes_roasted_salmon_plated_variants_to_hot_by_keyword(self) -> None:
        sections = [
            {
                "title": "Items",
                "type": "course",
                "service_role": "other",
                "course_type": "entree",
                "items": [
                    {"name": "Roasted Salmon with Mash Potatoes, Roasted Baby Carrots, Cajun Cream Sauce"},
                    {"name": "Roasted Salmon with Wild Rice and Asparagus"},
                ],
            }
        ]
        annotated = annotate_menu_sections_with_production(sections)
        items = {item["name"]: item["production_area"] for item in annotated[0]["items"]}
        self.assertEqual(
            items["Roasted Salmon with Mash Potatoes, Roasted Baby Carrots, Cajun Cream Sauce"]["temperature_zone"],
            "hot_kitchen",
        )
        self.assertEqual(
            items["Roasted Salmon with Mash Potatoes, Roasted Baby Carrots, Cajun Cream Sauce"]["reason"],
            "keyword_item_rule:roasted_salmon",
        )
        self.assertEqual(items["Roasted Salmon with Wild Rice and Asparagus"]["temperature_zone"], "hot_kitchen")

    def test_routes_brownie_variants_to_cold_by_keyword(self) -> None:
        sections = [
            {
                "title": "Items",
                "type": "course",
                "service_role": "other",
                "course_type": "other",
                "items": [
                    {"name": "Double Chocolate Brownies", "source_text": "(25) Double Chocolate Brownies @ $50.4 per Dozen"},
                    {"name": "Chocolate Brownie Bites", "source_text": "Chocolate Brownie Bites"},
                ],
            }
        ]
        annotated = annotate_menu_sections_with_production(sections)
        items = {item["name"]: item["production_area"] for item in annotated[0]["items"]}
        self.assertEqual(items["Double Chocolate Brownies"]["temperature_zone"], "cold_kitchen")
        self.assertEqual(items["Double Chocolate Brownies"]["reason"], "keyword_item_rule:brownie")
        self.assertEqual(items["Chocolate Brownie Bites"]["temperature_zone"], "cold_kitchen")

    def test_routes_lemon_bars_to_cold(self) -> None:
        sections = [
            {
                "title": "Items",
                "type": "course",
                "service_role": "other",
                "course_type": "other",
                "items": [
                    {"name": "Lemon Bars", "source_text": "(25) Lemon Bars @ $50.4 per Dozen"},
                ],
            }
        ]
        annotated = annotate_menu_sections_with_production(sections)
        item = annotated[0]["items"][0]
        self.assertEqual(item["production_area"]["temperature_zone"], "cold_kitchen")

    def test_routes_assorted_rolls_with_butter_to_hot(self) -> None:
        sections = [
            {
                "title": "Items",
                "type": "course",
                "service_role": "other",
                "course_type": "other",
                "items": [
                    {"name": "Assorted Rolls with Butter", "source_text": "Assorted Rolls with Butter"},
                ],
            }
        ]
        annotated = annotate_menu_sections_with_production(sections)
        item = annotated[0]["items"][0]
        self.assertEqual(item["production_area"]["temperature_zone"], "hot_kitchen")

    def test_routes_buffet_sides_and_cauliflower_to_hot(self) -> None:
        sections = [
            {
                "title": "Choice of Two Proteins:",
                "type": "course",
                "service_role": "other",
                "course_type": "other",
                "items": [
                    {"name": "Curry Roasted Cauliflower"},
                ],
            },
            {
                "title": "Sides",
                "type": "course",
                "service_role": "other",
                "course_type": "other",
                "items": [
                    {"name": "Garlic Mashed Potatoes"},
                    {"name": "Sauteed Green Beans"},
                ],
            },
        ]
        annotated = annotate_menu_sections_with_production(sections)
        first = annotated[0]["items"][0]
        second_items = {item["name"]: item["production_area"]["temperature_zone"] for item in annotated[1]["items"]}
        self.assertEqual(first["production_area"]["temperature_zone"], "hot_kitchen")
        self.assertEqual(second_items["Garlic Mashed Potatoes"], "hot_kitchen")
        self.assertEqual(second_items["Sauteed Green Beans"], "hot_kitchen")

    def test_routes_plated_rolls_and_entree_to_hot(self) -> None:
        sections = [
            {
                "title": "Items",
                "type": "course",
                "service_role": "other",
                "course_type": "other",
                "items": [
                    {"name": "Rolls with Butter"},
                    {"name": "Roasted Airline Chicken Breast with Herb Roasted Potatoes, Broccolini, and Lemon Thyme Jus"},
                ],
            }
        ]
        annotated = annotate_menu_sections_with_production(sections)
        items = {item["name"]: item["production_area"]["temperature_zone"] for item in annotated[0]["items"]}
        self.assertEqual(items["Rolls with Butter"], "hot_kitchen")
        self.assertEqual(
            items["Roasted Airline Chicken Breast with Herb Roasted Potatoes, Broccolini, and Lemon Thyme Jus"],
            "hot_kitchen",
        )

    def test_routes_assorted_sliced_cake_to_cold(self) -> None:
        sections = [
            {
                "title": "Dessert",
                "type": "course",
                "service_role": "other",
                "course_type": "dessert",
                "items": [
                    {"name": "Assorted Sliced Cake"},
                ],
            }
        ]
        annotated = annotate_menu_sections_with_production(sections)
        item = annotated[0]["items"][0]
        self.assertEqual(item["production_area"]["temperature_zone"], "cold_kitchen")

    def test_routes_plated_salad_and_generic_dessert_by_course_type(self) -> None:
        sections = [
            {
                "title": "Mixed Greens",
                "type": "course",
                "service_role": "other",
                "course_type": "salad",
                "items": [
                    {"name": "Cucumber"},
                    {"name": "Radish"},
                    {"name": "Balsamic Vinaigrette"},
                ],
            },
            {
                "title": "Chef's Choice Dessert",
                "type": "course",
                "service_role": "other",
                "course_type": "dessert",
                "items": [
                    {"name": "Two Types at Alternative Place Settings"},
                ],
            },
        ]
        annotated = annotate_menu_sections_with_production(sections)
        salad_items = {item["name"]: item["production_area"]["temperature_zone"] for item in annotated[0]["items"]}
        dessert_item = annotated[1]["items"][0]
        self.assertEqual(salad_items["Cucumber"], "cold_kitchen")
        self.assertEqual(salad_items["Radish"], "cold_kitchen")
        self.assertEqual(salad_items["Balsamic Vinaigrette"], "cold_kitchen")
        self.assertEqual(dessert_item["production_area"]["temperature_zone"], "cold_kitchen")


if __name__ == "__main__":
    unittest.main()
