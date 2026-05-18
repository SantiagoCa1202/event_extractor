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
                    {"name": "Spring Mix"},
                    {"name": "Cherry Tomato"},
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
        self.assertEqual(items["Spring Mix"], "cold_kitchen")
        self.assertEqual(items["Cherry Tomato"], "cold_kitchen")
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

    def test_routes_the_uptown_pastry_bundle_to_cold(self) -> None:
        sections = [
            {
                "title": "The Uptown",
                "type": "course",
                "service_role": "other",
                "course_type": "other",
                "items": [
                    {"name": "Breakfast Pastries", "source_text": "Breakfast Pastries, Croissants & Mini Biscuits with Strawberry and Apricot"},
                    {"name": "Croissants", "source_text": "Breakfast Pastries, Croissants & Mini Biscuits with Strawberry and Apricot"},
                    {"name": "Mini Biscuits", "source_text": "Breakfast Pastries, Croissants & Mini Biscuits with Strawberry and Apricot"},
                    {"name": "Strawberry", "source_text": "Breakfast Pastries, Croissants & Mini Biscuits with Strawberry and Apricot"},
                    {"name": "Apricot", "source_text": "Breakfast Pastries, Croissants & Mini Biscuits with Strawberry and Apricot"},
                ],
            }
        ]
        annotated = annotate_menu_sections_with_production(sections)
        items = {item["name"]: item["production_area"]["temperature_zone"] for item in annotated[0]["items"]}
        self.assertEqual(items["Breakfast Pastries"], "cold_kitchen")
        self.assertEqual(items["Croissants"], "cold_kitchen")
        self.assertEqual(items["Mini Biscuits"], "cold_kitchen")
        self.assertEqual(items["Strawberry"], "cold_kitchen")
        self.assertEqual(items["Apricot"], "cold_kitchen")

    def test_routes_mac_and_cheese_bites_to_hot(self) -> None:
        sections = [
            {
                "title": "Items",
                "type": "course",
                "service_role": "other",
                "course_type": "other",
                "items": [
                    {"name": "Mac & Cheese Bites", "source_text": "(350) Mac & Cheese Bites @ $5 Each"},
                ],
            }
        ]
        annotated = annotate_menu_sections_with_production(sections)
        item = annotated[0]["items"][0]
        self.assertEqual(item["name"], "Mac & Cheese Bites")
        self.assertEqual(item["production_area"]["temperature_zone"], "hot_kitchen")

    def test_routes_blue_moody_cheese_and_chestnut_honey_to_cold(self) -> None:
        sections = [
            {
                "title": "Items",
                "type": "course",
                "service_role": "other",
                "course_type": "other",
                "items": [
                    {"name": "Blue Moody Cheese", "source_text": "Blue Moody Cheese & Chestnut Honey"},
                    {"name": "Chestnut Honey", "source_text": "Blue Moody Cheese & Chestnut Honey"},
                ],
            }
        ]
        annotated = annotate_menu_sections_with_production(sections)
        items = {item["name"]: item["production_area"]["temperature_zone"] for item in annotated[0]["items"]}
        self.assertEqual(items["Blue Moody Cheese"], "cold_kitchen")
        self.assertEqual(items["Chestnut Honey"], "cold_kitchen")

    def test_routes_grilled_beef_coulotte_bundle_to_hot(self) -> None:
        sections = [
            {
                "title": "*CHEFS CARVING STATION*",
                "type": "station_items",
                "service_role": "station",
                "course_type": "other",
                "items": [
                    {"name": "Grilled Beef Coulotte, Chimichurri, Chipotle Aioli", "source_text": "Grilled Beef Coulotte, Chimichurri, Chipotle Aioli"},
                ],
            }
        ]
        annotated = annotate_menu_sections_with_production(sections)
        item = annotated[0]["items"][0]
        self.assertEqual(item["name"], "Grilled Beef Coulotte, Chimichurri, Chipotle Aioli")
        self.assertEqual(item["production_area"]["temperature_zone"], "hot_kitchen")

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

    def test_routes_consolidated_plated_choice_sections(self) -> None:
        sections = [
            {
                "title": "Preset Salad Choice",
                "type": "course",
                "service_role": "other",
                "course_type": "salad",
                "items": [
                    {
                        "name": "Baby Spinach Salad, Frisee, Strawberries, Goat Cheese, Candied Pecans, Strawberry Champagne Vinaigrette",
                    }
                ],
            },
            {
                "title": "Entree Choice",
                "type": "course",
                "service_role": "other",
                "course_type": "entree",
                "items": [
                    {
                        "name": "Beef Short Ribs and Seared Scallops\nStarch Choice: Whipped Potatoes\nVegetable Choice: Brocolini",
                    }
                ],
            },
            {
                "title": "Dessert Choice",
                "type": "course",
                "service_role": "other",
                "course_type": "dessert",
                "items": [
                    {
                        "name": "Hazel Nut Crunch Cake & Brule Cheesecake",
                    }
                ],
            },
        ]
        annotated = annotate_menu_sections_with_production(sections)
        self.assertEqual(annotated[0]["items"][0]["production_area"]["temperature_zone"], "cold_kitchen")
        self.assertEqual(annotated[1]["items"][0]["production_area"]["temperature_zone"], "hot_kitchen")
        self.assertEqual(annotated[2]["items"][0]["production_area"]["temperature_zone"], "cold_kitchen")

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

    def test_routes_manual_hot_and_cold_assignments_from_rules_file(self) -> None:
        sections = [
            {
                "title": "Items",
                "type": "course",
                "service_role": "other",
                "course_type": "other",
                "items": [
                    {"name": "Garlic & Chili Broccolini"},
                    {"name": "Creamy Mac & Cheese"},
                    {"name": "Pico de Gallo"},
                    {"name": "Queen City Pimento Cheese"},
                    {"name": "Stuffed Mushrooms"},
                    {"name": "Bacon Wrapped Scallops"},
                ],
            }
        ]
        annotated = annotate_menu_sections_with_production(sections)
        items = {item["name"]: item["production_area"]["temperature_zone"] for item in annotated[0]["items"]}
        self.assertEqual(items["Garlic & Chili Broccolini"], "hot_kitchen")
        self.assertEqual(items["Creamy Mac & Cheese"], "hot_kitchen")
        self.assertEqual(items["Pico de Gallo"], "cold_kitchen")
        self.assertEqual(items["Queen City Pimento Cheese"], "cold_kitchen")
        self.assertEqual(items["Stuffed Mushrooms"], "hot_kitchen")
        self.assertEqual(items["Bacon Wrapped Scallops"], "hot_kitchen")

    def test_routes_new_cold_items_from_manual_rules(self) -> None:
        sections = [
            {
                "title": "Items",
                "type": "course",
                "service_role": "other",
                "course_type": "other",
                "items": [
                    {"name": "Fresh Whole Fruit"},
                    {"name": "Queen City Pimento Cheese with Butter Cracker"},
                    {"name": "Rold Gold Mini Pretzel"},
                ],
            }
        ]
        annotated = annotate_menu_sections_with_production(sections)
        items = {item["name"]: item["production_area"]["temperature_zone"] for item in annotated[0]["items"]}
        self.assertEqual(items["Fresh Whole Fruit"], "cold_kitchen")
        self.assertEqual(items["Queen City Pimento Cheese with Butter Cracker"], "cold_kitchen")
        self.assertEqual(items["Rold Gold Mini Pretzel"], "cold_kitchen")

    def test_routes_down_south_boulevard_items(self) -> None:
        sections = [
            {
                "title": "Choice of Two Proteins:",
                "type": "course",
                "service_role": "other",
                "course_type": "other",
                "items": [
                    {"name": "Flank Steak with Chimichurri,"},
                    {"name": "Flounder a la Veracruz"},
                    {"name": "Cilantro Lime Rice"},
                    {"name": "Charros Beans"},
                ],
            },
            {
                "title": "Dessert",
                "type": "course",
                "service_role": "other",
                "course_type": "dessert",
                "items": [
                    {"name": "Assorted Sliced Cake"},
                ],
            },
            {
                "title": "Items",
                "type": "course",
                "service_role": "other",
                "course_type": "other",
                "items": [
                    {"name": "Chile Rellenos with Ranchero Sauce", "source_text": "(70) Chile Rellenos with Ranchero Sauce @ $6"},
                ],
            },
        ]
        annotated = annotate_menu_sections_with_production(sections)
        proteins = {item["name"]: item["production_area"]["temperature_zone"] for item in annotated[0]["items"]}
        self.assertEqual(proteins["Flank Steak with Chimichurri,"], "hot_kitchen")
        self.assertEqual(proteins["Flounder a la Veracruz"], "hot_kitchen")
        self.assertEqual(proteins["Cilantro Lime Rice"], "hot_kitchen")
        self.assertEqual(proteins["Charros Beans"], "hot_kitchen")
        self.assertEqual(annotated[1]["items"][0]["production_area"]["temperature_zone"], "cold_kitchen")
        self.assertEqual(annotated[2]["items"][0]["production_area"]["temperature_zone"], "hot_kitchen")

    def test_routes_mason_jar_caesar_to_cold(self) -> None:
        sections = [
            {
                "title": "Items",
                "type": "course",
                "service_role": "other",
                "course_type": "other",
                "items": [
                    {
                        "name": "Mason Jar Caesar",
                        "quantity": 120,
                        "notes": "Baby Gem, Parmesan, Roasted | Tomato, Garlic Croutons | Caesar Dressing",
                        "source_text": "(120) Mason Jar Caesar @ $10",
                    },
                ],
            }
        ]
        annotated = annotate_menu_sections_with_production(sections)
        item = annotated[0]["items"][0]
        self.assertEqual(item["production_area"]["temperature_zone"], "cold_kitchen")

    def test_routes_carolina_bbq_buffet_items(self) -> None:
        sections = [
            {
                "title": "Carolina BBQ Buffet",
                "type": "course",
                "service_role": "other",
                "course_type": "other",
                "items": [{"name": "Sweet Rolls with Butter"}],
            },
            {
                "title": "Greens",
                "type": "cold_items",
                "service_role": "buffet",
                "course_type": "salad",
                "items": [
                    {"name": "Spring Mix"},
                    {"name": "Cherry Tomato"},
                    {"name": "Cucumber"},
                    {"name": "Shredded Carrot"},
                    {"name": "Cheddar"},
                    {"name": "Black Olives"},
                    {"name": "Croutons"},
                    {"name": "Buttermilk Ranch Dressing"},
                    {"name": "White Balsamic Dressing"},
                ],
            },
            {
                "title": "Cold",
                "type": "course",
                "service_role": "other",
                "course_type": "other",
                "items": [{"name": "Coleslaw"}],
            },
            {
                "title": "Choice of Two Proteins:",
                "type": "course",
                "service_role": "other",
                "course_type": "other",
                "items": [
                    {"name": "North Carolina Smoked Pulled Pork"},
                    {"name": "Smoked Brisket"},
                    {"name": "BBQ Rub Shrimp"},
                ],
            },
            {
                "title": "Sides",
                "type": "course",
                "service_role": "other",
                "course_type": "other",
                "items": [
                    {"name": "Creamy Mac & Cheese"},
                    {"name": "BBQ Baked Beans"},
                ],
            },
        ]
        annotated = annotate_menu_sections_with_production(sections)
        greens = {item["name"]: item["production_area"]["temperature_zone"] for item in annotated[1]["items"]}
        proteins = {item["name"]: item["production_area"]["temperature_zone"] for item in annotated[3]["items"]}
        sides = {item["name"]: item["production_area"]["temperature_zone"] for item in annotated[4]["items"]}
        self.assertEqual(annotated[0]["items"][0]["production_area"]["temperature_zone"], "hot_kitchen")
        self.assertEqual(greens["Spring Mix"], "cold_kitchen")
        self.assertEqual(greens["Buttermilk Ranch Dressing"], "cold_kitchen")
        self.assertEqual(annotated[2]["items"][0]["production_area"]["temperature_zone"], "cold_kitchen")
        self.assertEqual(proteins["North Carolina Smoked Pulled Pork"], "hot_kitchen")
        self.assertEqual(proteins["Smoked Brisket"], "hot_kitchen")
        self.assertEqual(proteins["BBQ Rub Shrimp"], "hot_kitchen")
        self.assertEqual(sides["Creamy Mac & Cheese"], "hot_kitchen")
        self.assertEqual(sides["BBQ Baked Beans"], "hot_kitchen")

    def test_routes_queens_table_items(self) -> None:
        sections = [
            {
                "title": "The Queens Table",
                "type": "course",
                "service_role": "other",
                "course_type": "other",
                "items": [{"name": "Assorted Rolls with Butter"}],
            },
            {
                "title": "Greens",
                "type": "cold_items",
                "service_role": "buffet",
                "course_type": "salad",
                "items": [
                    {"name": "Baby Spinach"},
                    {"name": "Cherry Tomato"},
                    {"name": "Cucumber"},
                    {"name": "Shredded Carrot"},
                    {"name": "Shredded Cheddar"},
                    {"name": "Black Olives"},
                    {"name": "Buttermilk Ranch"},
                    {"name": "White Balsamic Dressing"},
                ],
            },
            {
                "title": "Choice of Two Proteins:",
                "type": "course",
                "service_role": "other",
                "course_type": "other",
                "items": [
                    {"name": "Steak Medallions with Red Wine Reduction,"},
                    {"name": "Seared Salmon with a Cajun Cream Sauce"},
                ],
            },
            {
                "title": "Sides",
                "type": "course",
                "service_role": "other",
                "course_type": "other",
                "items": [{"name": "Cauliflower"}],
            },
        ]
        annotated = annotate_menu_sections_with_production(sections)
        greens = {item["name"]: item["production_area"]["temperature_zone"] for item in annotated[1]["items"]}
        proteins = {item["name"]: item["production_area"]["temperature_zone"] for item in annotated[2]["items"]}
        self.assertEqual(annotated[0]["items"][0]["production_area"]["temperature_zone"], "hot_kitchen")
        self.assertEqual(greens["Baby Spinach"], "cold_kitchen")
        self.assertEqual(greens["White Balsamic Dressing"], "cold_kitchen")
        self.assertEqual(proteins["Steak Medallions with Red Wine Reduction,"], "hot_kitchen")
        self.assertEqual(proteins["Seared Salmon with a Cajun Cream Sauce"], "hot_kitchen")
        self.assertEqual(annotated[3]["items"][0]["production_area"]["temperature_zone"], "hot_kitchen")

    def test_routes_seared_salmon_with_cajun_cream_sauce_variant_to_hot(self) -> None:
        sections = [
            {
                "title": "Choice of Two Proteins:",
                "type": "course",
                "service_role": "other",
                "course_type": "other",
                "items": [
                    {"name": "Seared Salmon With Cajun Cream Sauce"},
                ],
            }
        ]
        annotated = annotate_menu_sections_with_production(sections)
        item = annotated[0]["items"][0]
        self.assertEqual(item["production_area"]["temperature_zone"], "hot_kitchen")

    def test_routes_passed_hot_items_even_with_literal_prefix(self) -> None:
        sections = [
            {
                "title": "Passed",
                "type": "course",
                "service_role": "other",
                "course_type": "other",
                "items": [
                    {"name": "(Passed) Stuffed Mushrooms"},
                    {"name": "(Passed) Shrimp Cocktail (4 pieces of shrimp per order)"},
                    {"name": "(Passed) Beef Filet"},
                    {"name": "(Passed) Bacon Wrapped Scallops"},
                ],
            }
        ]
        annotated = annotate_menu_sections_with_production(sections)
        items = {item["name"]: item["production_area"]["temperature_zone"] for item in annotated[0]["items"]}
        self.assertEqual(items["(Passed) Stuffed Mushrooms"], "hot_kitchen")
        self.assertEqual(items["(Passed) Shrimp Cocktail (4 pieces of shrimp per order)"], "hot_kitchen")
        self.assertEqual(items["(Passed) Beef Filet"], "hot_kitchen")
        self.assertEqual(items["(Passed) Bacon Wrapped Scallops"], "hot_kitchen")

    def test_routes_pimento_shrimp_bruschetta_to_hot(self) -> None:
        sections = [
            {
                "title": "Displayed",
                "type": "course",
                "service_role": "other",
                "course_type": "other",
                "items": [
                    {
                        "name": "Pimento Cheese & Pickled Shrimp Bruschetta Crostini",
                        "quantity": 650,
                        "unit": "each",
                        "source_text": "(650) (Displayed) Pimento Cheese & Pickled Shrimp Bruschetta Crostini @ $9.9 Each",
                    }
                ],
            }
        ]
        annotated = annotate_menu_sections_with_production(sections)
        item = annotated[0]["items"][0]
        self.assertEqual(item["production_area"]["temperature_zone"], "hot_kitchen")

    def test_ignored_manual_items_do_not_appear_in_operational_split(self) -> None:
        sections = [
            {
                "title": "Items",
                "type": "course",
                "service_role": "other",
                "course_type": "other",
                "items": [
                    {"name": "Soft Drinks and Bottled Water"},
                    {"name": "Complimentary per contract"},
                    {"name": "Pico de Gallo"},
                ],
            }
        ]
        annotated = annotate_menu_sections_with_production(sections)
        names = [item["name"] for item in annotated[0]["items"]]
        self.assertEqual(names, ["Pico de Gallo"])
        self.assertEqual(annotated[0]["operational_split"]["cold_kitchen_items"], ["Pico de Gallo"])

    def test_routes_popcorn_flavors_to_cold_by_source_context(self) -> None:
        sections = [
            {
                "title": "Snacks",
                "type": "snack_items",
                "service_role": "break",
                "course_type": "other",
                "items": [
                    {"name": "Butter", "source_text": "Popcorn - Butter, Jalapeno, Kettle"},
                    {"name": "Jalapeno", "source_text": "Popcorn - Butter, Jalapeno, Kettle"},
                    {"name": "Kettle", "source_text": "Popcorn - Butter, Jalapeno, Kettle"},
                ],
            }
        ]
        annotated = annotate_menu_sections_with_production(sections)
        items = {item["name"]: item["production_area"]["temperature_zone"] for item in annotated[0]["items"]}
        self.assertEqual(items["Butter"], "cold_kitchen")
        self.assertEqual(items["Jalapeno"], "cold_kitchen")
        self.assertEqual(items["Kettle"], "cold_kitchen")

    def test_routes_mini_corndogs_hot_and_condiments_cold(self) -> None:
        sections = [
            {
                "title": "Passed",
                "type": "course",
                "service_role": "other",
                "course_type": "other",
                "items": [
                    {"name": "Mini Corndogs"},
                    {"name": "Ketchup"},
                    {"name": "Mustard"},
                ],
            }
        ]
        annotated = annotate_menu_sections_with_production(sections)
        items = {item["name"]: item["production_area"]["temperature_zone"] for item in annotated[0]["items"]}
        self.assertEqual(items["Mini Corndogs"], "hot_kitchen")
        self.assertEqual(items["Ketchup"], "cold_kitchen")
        self.assertEqual(items["Mustard"], "cold_kitchen")

    def test_routes_selection_of_rolls_and_butter_to_hot(self) -> None:
        sections = [
            {
                "title": "Items",
                "type": "course",
                "service_role": "other",
                "course_type": "other",
                "items": [
                    {"name": "Selection of Rolls and Butter"},
                ],
            }
        ]
        annotated = annotate_menu_sections_with_production(sections)
        item = annotated[0]["items"][0]
        self.assertEqual(item["production_area"]["temperature_zone"], "hot_kitchen")

    def test_ignores_upon_requests_and_routes_accoutrement_and_buffalo_sauce_cold(self) -> None:
        sections = [
            {
                "title": "Items",
                "type": "course",
                "service_role": "other",
                "course_type": "other",
                "items": [
                    {"name": "Upon Requests :"},
                    {"name": "Accoutrement"},
                    {"name": "Buffalo Sauce", "source_text": "Buffalo Sauce on Side"},
                ],
            }
        ]
        annotated = annotate_menu_sections_with_production(sections)
        names = [item["name"] for item in annotated[0]["items"]]
        items = {item["name"]: item["production_area"]["temperature_zone"] for item in annotated[0]["items"]}
        self.assertEqual(names, ["Accoutrement", "Buffalo Sauce"])
        self.assertEqual(items["Accoutrement"], "cold_kitchen")
        self.assertEqual(items["Buffalo Sauce"], "cold_kitchen")

    def test_ignores_selection_of_hot_tazo_teas(self) -> None:
        sections = [
            {
                "title": "Beverages Charged on Consumption",
                "type": "course",
                "service_role": "other",
                "course_type": "beverage",
                "items": [
                    {
                        "name": "a selection of hot Tazo Teas",
                        "source_text": "Freshly brewed Starbucks Regular and Decaffeinated Coffee, and a selection of hot Tazo Teas",
                    }
                ],
            }
        ]
        annotated = annotate_menu_sections_with_production(sections)
        self.assertEqual(annotated[0]["items"], [])
        self.assertEqual(annotated[0]["operational_split"]["unknown_items"], [])

    def test_routes_boxed_lunch_choices_to_cold(self) -> None:
        sections = [
            {
                "title": "Boxed Lunch",
                "type": "course",
                "service_role": "other",
                "course_type": "other",
                "items": [
                    {"name": "Smoke Master", "quantity": 14},
                    {"name": "Ovengold Turkey", "quantity": 45},
                    {"name": "Caesar BLT Wrap", "quantity": 45},
                ],
            }
        ]
        annotated = annotate_menu_sections_with_production(sections)
        items = {item["name"]: item["production_area"]["temperature_zone"] for item in annotated[0]["items"]}
        self.assertEqual(items["Smoke Master"], "cold_kitchen")
        self.assertEqual(items["Ovengold Turkey"], "cold_kitchen")
        self.assertEqual(items["Caesar BLT Wrap"], "cold_kitchen")

    def test_routes_deli_buffet_sections_to_cold(self) -> None:
        sections = [
            {
                "title": "Boards Head Meats",
                "type": "course",
                "service_role": "other",
                "course_type": "other",
                "items": [
                    {"name": "Turkey"},
                    {"name": "Ham"},
                    {"name": "Mortadella"},
                    {"name": "Chicken Salad"},
                ],
            },
            {
                "title": "Cheese",
                "type": "course",
                "service_role": "other",
                "course_type": "other",
                "items": [
                    {"name": "Smoked Gouda"},
                    {"name": "Sharp Cheddar"},
                ],
            },
        ]
        annotated = annotate_menu_sections_with_production(sections)
        meat_items = {item["name"]: item["production_area"]["temperature_zone"] for item in annotated[0]["items"]}
        cheese_items = {item["name"]: item["production_area"]["temperature_zone"] for item in annotated[1]["items"]}
        self.assertEqual(meat_items["Turkey"], "cold_kitchen")
        self.assertEqual(meat_items["Ham"], "cold_kitchen")
        self.assertEqual(meat_items["Mortadella"], "cold_kitchen")
        self.assertEqual(meat_items["Chicken Salad"], "cold_kitchen")
        self.assertEqual(cheese_items["Smoked Gouda"], "cold_kitchen")
        self.assertEqual(cheese_items["Sharp Cheddar"], "cold_kitchen")

    def test_routes_slider_display_items_hot_and_cold(self) -> None:
        sections = [
            {
                "title": "Slider Display",
                "type": "display",
                "service_role": "display",
                "course_type": "other",
                "items": [
                    {"name": "Mini Cheeseburgers"},
                    {"name": "Brioche Buns"},
                    {"name": "BBQ Pulled Pork"},
                    {"name": "Hawaiian Buns"},
                    {"name": "Green Tomato"},
                    {"name": "Pimento Cheese"},
                    {"name": "Chipotle Ketchup"},
                    {"name": "Cornichon"},
                    {"name": "Pickled Onion"},
                ],
            }
        ]
        annotated = annotate_menu_sections_with_production(sections)
        items = {item["name"]: item["production_area"]["temperature_zone"] for item in annotated[0]["items"]}
        self.assertEqual(items["Mini Cheeseburgers"], "hot_kitchen")
        self.assertEqual(items["Brioche Buns"], "hot_kitchen")
        self.assertEqual(items["BBQ Pulled Pork"], "hot_kitchen")
        self.assertEqual(items["Hawaiian Buns"], "hot_kitchen")
        self.assertEqual(items["Green Tomato"], "cold_kitchen")
        self.assertEqual(items["Pimento Cheese"], "cold_kitchen")
        self.assertEqual(items["Chipotle Ketchup"], "cold_kitchen")
        self.assertEqual(items["Cornichon"], "cold_kitchen")
        self.assertEqual(items["Pickled Onion"], "cold_kitchen")

    def test_routes_new_items_from_unknown_items_review_file(self) -> None:
        sections = [
            {
                "title": "Custom Lunch Menu",
                "type": "course",
                "service_role": "other",
                "course_type": "other",
                "items": [
                    {"name": "Corn & Black Bean Salad"},
                    {"name": "Black Bean Salad"},
                    {"name": "Beans"},
                    {"name": "Buttered Noodles"},
                    {"name": "Hard and Soft Taco Shells"},
                    {"name": "Salsa"},
                    {"name": "Shredded Cheese"},
                    {"name": "Tomato", "source_text": "Shredded Cheese, Lettuce, Tomato, Onion, Salsa"},
                    {"name": "Onion", "source_text": "Shredded Cheese, Lettuce, Tomato, Onion, Salsa"},
                ],
            },
            {
                "title": "Items",
                "type": "course",
                "service_role": "other",
                "course_type": "other",
                "items": [
                    {"name": "1 Gallon of Each"},
                    {"name": "Plated Lunch (Salad and Dessert Pre-Set by 11:15am"},
                    {"name": "Tea Bag Assortment"},
                ],
            },
        ]
        annotated = annotate_menu_sections_with_production(sections)
        custom = {item["name"]: item["production_area"]["temperature_zone"] for item in annotated[0]["items"]}
        self.assertEqual(custom["Corn & Black Bean Salad"], "cold_kitchen")
        self.assertEqual(custom["Black Bean Salad"], "cold_kitchen")
        self.assertEqual(custom["Beans"], "hot_kitchen")
        self.assertEqual(custom["Buttered Noodles"], "hot_kitchen")
        self.assertEqual(custom["Hard and Soft Taco Shells"], "hot_kitchen")
        self.assertEqual(custom["Salsa"], "cold_kitchen")
        self.assertEqual(custom["Shredded Cheese"], "cold_kitchen")
        self.assertEqual(custom["Tomato"], "cold_kitchen")
        self.assertEqual(custom["Onion"], "cold_kitchen")
        self.assertEqual(annotated[1]["items"], [])

    def test_routes_recent_unknown_review_items_and_compound_patterns(self) -> None:
        sections = [
            {
                "title": "Items",
                "type": "course",
                "service_role": "other",
                "course_type": "other",
                "items": [
                    {"name": "Mac & Cheese"},
                    {"name": "Garlic & Cajun Shrimp"},
                    {"name": "Butternut Squash Ravioli - Brown Butter, Pecans, Crispy Sage"},
                    {"name": "Spinach, Mushroom, Onion, Garlic Cream Sauce"},
                    {"name": "Soup du Jour (tomato soup)"},
                    {"name": "Assorted Petite Fours - Individual Desserts"},
                    {"name": "Hardboiled Egg"},
                    {"name": "Marinated Grilled Vegetables"},
                    {"name": "White Balsamic Vinegarette"},
                ],
            }
        ]
        annotated = annotate_menu_sections_with_production(sections)
        items = {item["name"]: item["production_area"]["temperature_zone"] for item in annotated[0]["items"]}
        self.assertEqual(items["Mac & Cheese"], "hot_kitchen")
        self.assertEqual(items["Garlic & Cajun Shrimp"], "hot_kitchen")
        self.assertEqual(items["Butternut Squash Ravioli - Brown Butter, Pecans, Crispy Sage"], "hot_kitchen")
        self.assertEqual(items["Spinach, Mushroom, Onion, Garlic Cream Sauce"], "hot_kitchen")
        self.assertEqual(items["Soup du Jour (tomato soup)"], "hot_kitchen")
        self.assertEqual(items["Assorted Petite Fours - Individual Desserts"], "cold_kitchen")
        self.assertEqual(items["Hardboiled Egg"], "cold_kitchen")
        self.assertEqual(items["Marinated Grilled Vegetables"], "cold_kitchen")
        self.assertEqual(items["White Balsamic Vinegarette"], "cold_kitchen")

    def test_routes_batch_items_from_unknown_review_file(self) -> None:
        sections = [
            {
                "title": "Items",
                "type": "course",
                "service_role": "other",
                "course_type": "other",
                "items": [
                    {"name": "Assorted Cake Pops"},
                    {"name": "French Macarons"},
                    {"name": "Krispy Kreme Glazed Donuts"},
                    {"name": "Mini Fruit Skewers"},
                    {"name": "Mango Salad Cups"},
                    {"name": "Vegetable Shooters with Hummus"},
                    {"name": "Buffalo Pizza"},
                    {"name": "Penne Pasta alla Vodka"},
                    {"name": "Mini BBQ Slider"},
                    {"name": "Pigs in A Blanket"},
                    {"name": "Sweet Tea and Iced Water"},
                    {"name": "Faculty Beverage Station"},
                    {"name": "All About The Movies"},
                    {"name": "Bubly Flavored Sparkling Water"},
                    {"name": "Set in foyer to start at 9a"},
                    {"name": "Potato Salad &"},
                    {"name": "Kettle Chips"},
                    {"name": "Hard Boiled Eggs"},
                    {"name": "Fresh Cut Fruit"},
                ],
            },
            {
                "title": "Charcuterie Display",
                "type": "display",
                "service_role": "display",
                "course_type": "other",
                "items": [
                    {"name": "Prosciutto"},
                    {"name": "Hot Coppa"},
                    {"name": "Pickled Okra"},
                    {"name": "Whole Grain Mustard"},
                ],
            },
            {
                "title": "Chips and Dips Pairing",
                "type": "course",
                "service_role": "other",
                "course_type": "other",
                "items": [
                    {"name": "Homemade Salsa"},
                    {"name": "Sour Cream Chive Dip"},
                    {"name": "Queen City Bacon Pimento Cheese"},
                ],
            },
            {
                "title": "The Uptown",
                "type": "course",
                "service_role": "other",
                "course_type": "other",
                "items": [
                    {"name": "Banana", "source_text": "Banana, Strawberry, Vanilla Yogurt"},
                    {"name": "Strawberry", "source_text": "Banana, Strawberry, Vanilla Yogurt"},
                    {"name": "Vanilla Yogurt", "source_text": "Banana, Strawberry, Vanilla Yogurt"},
                    {"name": "Agave", "source_text": "Mixed Berries, Agave"},
                ],
            },
        ]
        annotated = annotate_menu_sections_with_production(sections)
        items = {item["name"]: item["production_area"]["temperature_zone"] for item in annotated[0]["items"]}
        self.assertEqual(items["Assorted Cake Pops"], "cold_kitchen")
        self.assertEqual(items["French Macarons"], "cold_kitchen")
        self.assertEqual(items["Krispy Kreme Glazed Donuts"], "cold_kitchen")
        self.assertEqual(items["Mini Fruit Skewers"], "cold_kitchen")
        self.assertEqual(items["Mango Salad Cups"], "cold_kitchen")
        self.assertEqual(items["Vegetable Shooters with Hummus"], "cold_kitchen")
        self.assertEqual(items["Buffalo Pizza"], "hot_kitchen")
        self.assertEqual(items["Penne Pasta alla Vodka"], "hot_kitchen")
        self.assertEqual(items["Mini BBQ Slider"], "hot_kitchen")
        self.assertEqual(items["Pigs in A Blanket"], "hot_kitchen")
        remaining_item_names = [item["name"] for item in annotated[0]["items"]]
        self.assertNotIn("Sweet Tea and Iced Water", remaining_item_names)
        self.assertNotIn("Faculty Beverage Station", remaining_item_names)
        self.assertNotIn("All About The Movies", remaining_item_names)
        self.assertNotIn("Bubly Flavored Sparkling Water", remaining_item_names)
        self.assertNotIn("Set in foyer to start at 9a", remaining_item_names)
        display_items = {item["name"]: item["production_area"]["temperature_zone"] for item in annotated[1]["items"]}
        self.assertEqual(display_items["Prosciutto"], "cold_kitchen")
        self.assertEqual(display_items["Hot Coppa"], "cold_kitchen")
        self.assertEqual(display_items["Pickled Okra"], "cold_kitchen")
        self.assertEqual(display_items["Whole Grain Mustard"], "cold_kitchen")
        dip_items = {item["name"]: item["production_area"]["temperature_zone"] for item in annotated[2]["items"]}
        self.assertEqual(dip_items["Homemade Salsa"], "cold_kitchen")
        self.assertEqual(dip_items["Sour Cream Chive Dip"], "cold_kitchen")
        self.assertEqual(dip_items["Queen City Bacon Pimento Cheese"], "cold_kitchen")
        smoothie_items = {item["name"]: item["production_area"]["temperature_zone"] for item in annotated[3]["items"]}
        self.assertEqual(smoothie_items["Banana"], "cold_kitchen")
        self.assertEqual(smoothie_items["Strawberry"], "cold_kitchen")
        self.assertEqual(smoothie_items["Vanilla Yogurt"], "cold_kitchen")
        self.assertEqual(smoothie_items["Agave"], "cold_kitchen")

    def test_does_not_route_dietary_restriction_onion_as_cold_food(self) -> None:
        sections = [
            {
                "title": "Items",
                "type": "course",
                "service_role": "other",
                "course_type": "other",
                "items": [
                    {"name": "Onion", "source_text": "Gluten, Garlic, Onion, Cashew, Shellfish, Beef - Suzan H."},
                ],
            }
        ]
        annotated = annotate_menu_sections_with_production(sections)
        item = annotated[0]["items"][0]
        self.assertEqual(item["production_area"]["temperature_zone"], "unknown")

    def test_routes_special_dietary_items_to_dietary_zone(self) -> None:
        sections = [
            {
                "title": "Items",
                "type": "course",
                "service_role": "other",
                "course_type": "other",
                "items": [
                    {"name": "4 Vegan", "source_text": "4 Vegan"},
                    {"name": "5 Vegetarian", "source_text": "5 Vegetarian"},
                    {"name": "1 Dairy Free", "source_text": "1 Dairy Free"},
                    {"name": "1 Peanut Allergy", "source_text": "1 Peanut Allergy"},
                    {"name": "1 Tree Nut Allergy", "source_text": "1 Tree Nut Allergy"},
                ],
            }
        ]
        annotated = annotate_menu_sections_with_production(sections)
        items = {item["name"]: item["production_area"]["temperature_zone"] for item in annotated[0]["items"]}
        self.assertEqual(items["4 Vegan"], "dietary")
        self.assertEqual(items["5 Vegetarian"], "dietary")
        self.assertEqual(items["1 Dairy Free"], "dietary")
        self.assertEqual(items["1 Peanut Allergy"], "dietary")
        self.assertEqual(items["1 Tree Nut Allergy"], "dietary")
        self.assertEqual(
            annotated[0]["operational_split"]["dietary_items"],
            ["4 Vegan", "5 Vegetarian", "1 Dairy Free", "1 Peanut Allergy", "1 Tree Nut Allergy"],
        )
        self.assertEqual(annotated[0]["operational_split"]["unknown_items"], [])

    def test_routes_special_dietary_salad_items_to_dietary_zone(self) -> None:
        sections = [
            {
                "title": "Items",
                "type": "course",
                "service_role": "other",
                "course_type": "other",
                "items": [
                    {"name": "4 vegan salads", "source_text": "4 vegan salads"},
                    {"name": "1 vegetarian salad", "source_text": "1 vegetarian salad"},
                    {"name": "1 dairy free salad", "source_text": "1 dairy free salad"},
                    {"name": "2 no pecan salad", "source_text": "2 no pecan salad"},
                ],
            }
        ]
        annotated = annotate_menu_sections_with_production(sections)
        items = {item["name"]: item["production_area"]["temperature_zone"] for item in annotated[0]["items"]}
        self.assertEqual(items["4 vegan salads"], "dietary")
        self.assertEqual(items["1 vegetarian salad"], "dietary")
        self.assertEqual(items["1 dairy free salad"], "dietary")
        self.assertEqual(items["2 no pecan salad"], "dietary")
        self.assertEqual(
            annotated[0]["operational_split"]["dietary_items"],
            ["4 vegan salads", "1 vegetarian salad", "1 dairy free salad", "2 no pecan salad"],
        )
        self.assertEqual(annotated[0]["operational_split"]["unknown_items"], [])

    def test_routes_pop_up_concessions_pattern(self) -> None:
        sections = [
            {
                "title": "Items",
                "type": "course",
                "service_role": "other",
                "course_type": "other",
                "items": [
                    {"name": "Assorted Candy Bars"},
                    {"name": "Assorted Fruit Cups"},
                    {"name": "Bags of Chips"},
                    {"name": "Basket of French Fries"},
                    {"name": "Chicken Caesar Salad"},
                    {"name": "Chicken Tenders with a Side (Fries, Chips, or Whole Fruit)"},
                    {"name": "Hamburger with a Side (Fries, Chips, or Whole Fruit)"},
                    {"name": "Large Mixed Greens Salad"},
                    {"name": "Protein/Granola Bars (2)"},
                    {"name": "Turkey Wrap with a Side (Fries, Chips, or Whole Fruit)"},
                    {"name": "Whole Fruit (1)"},
                    {"name": "Whole Fruit (2)"},
                    {"name": "Gatorade"},
                    {"name": "Mimosa"},
                    {"name": "Red Bull"},
                    {"name": "Soft Drinks"},
                    {"name": "Beverages and snacks open at 10am"},
                    {"name": "Concessions end at 1pm"},
                    {"name": "Food opens at 11am"},
                ],
            }
        ]
        annotated = annotate_menu_sections_with_production(sections)
        items = {item["name"]: item["production_area"]["temperature_zone"] for item in annotated[0]["items"]}
        self.assertEqual(items["Assorted Candy Bars"], "cold_kitchen")
        self.assertEqual(items["Assorted Fruit Cups"], "cold_kitchen")
        self.assertEqual(items["Bags of Chips"], "cold_kitchen")
        self.assertEqual(items["Basket of French Fries"], "hot_kitchen")
        self.assertEqual(items["Chicken Caesar Salad"], "cold_kitchen")
        self.assertEqual(items["Chicken Tenders with a Side (Fries, Chips, or Whole Fruit)"], "hot_kitchen")
        self.assertEqual(items["Hamburger with a Side (Fries, Chips, or Whole Fruit)"], "hot_kitchen")
        self.assertEqual(items["Large Mixed Greens Salad"], "cold_kitchen")
        self.assertEqual(items["Protein/Granola Bars (2)"], "cold_kitchen")
        self.assertEqual(items["Whole Fruit (1)"], "cold_kitchen")
        self.assertEqual(items["Whole Fruit (2)"], "cold_kitchen")
        remaining_item_names = [item["name"] for item in annotated[0]["items"]]
        self.assertNotIn("Gatorade", remaining_item_names)
        self.assertNotIn("Mimosa", remaining_item_names)
        self.assertNotIn("Red Bull", remaining_item_names)
        self.assertNotIn("Soft Drinks", remaining_item_names)
        self.assertNotIn("Beverages and snacks open at 10am", remaining_item_names)
        self.assertNotIn("Concessions end at 1pm", remaining_item_names)
        self.assertNotIn("Food opens at 11am", remaining_item_names)

    def test_routes_may_unknown_review_batch_without_unknowns(self) -> None:
        sections = [
            {
                "title": "Items",
                "type": "course",
                "service_role": "other",
                "course_type": "other",
                "items": [
                    {"name": "(__) Grilled Chicken with Cajun Cream Sauce"},
                    {"name": "(__) Salmon with Miso Yaki Sauce *no sesame seeds"},
                    {"name": "BBQ Chicken Thigh"},
                    {"name": "Black Beans", "source_text": "Spring Mix, Roasted Corn, Black Beans, Red Onion, Tortilla Strips"},
                    {"name": "Brulee Cheesecake"},
                    {"name": "Chipotle Ranch & White Balsamic (Set on Tables)"},
                    {"name": "Citrus Polla Asado, Chile Rellenos with Ranchero Sauce"},
                    {"name": "Coffee Cake"},
                    {"name": "Grilled Chicken Breast with Chimichurri Sauce, Cilantro Lime Rice, and Charro Beans (GF, DF)"},
                    {"name": "Lemon Butter Asparagus"},
                    {"name": "Mashed Potatoes"},
                    {"name": "Pork Loin Marsala"},
                    {"name": "Red Onion", "source_text": "Spring Mix, Roasted Corn, Black Beans, Red Onion, Tortilla Strips"},
                    {"name": "Roasted Corn", "source_text": "Spring Mix, Roasted Corn, Black Beans, Red Onion, Tortilla Strips"},
                    {"name": "Roasted Lemon with Thyme Chicken Breast"},
                    {"name": "Scones"},
                    {"name": "Strawberry Cheesecake - Preset"},
                    {"name": "Sugar Biscuits"},
                    {"name": "Tortilla Strips", "source_text": "Spring Mix, Roasted Corn, Black Beans, Red Onion, Tortilla Strips"},
                    {"name": "1 Decaf"},
                    {"name": "1 Tea"},
                    {"name": "1) Cucumber Mint Cooler - Lemonade"},
                    {"name": "10 In Back"},
                    {"name": "Comp Snacks for Up to 10 Staff Members"},
                    {"name": "Decaf Coffee (Group Providing Own Coffee Sleeves- No Starbucks Branding)"},
                    {"name": "Honey Syrup and Sparking Water"},
                    {"name": "Rotating"},
                    {"name": "The Uptown (Small Group Pricing) TBD- Plated Instead?"},
                    {"name": "Yellow Tables on Diagram NOT Pre-set"},
                ],
            }
        ]

        annotated = annotate_menu_sections_with_production(sections)
        items = {item["name"]: item["production_area"]["temperature_zone"] for item in annotated[0]["items"]}
        self.assertEqual(items["(__) Grilled Chicken with Cajun Cream Sauce"], "hot_kitchen")
        self.assertEqual(items["(__) Salmon with Miso Yaki Sauce *no sesame seeds"], "hot_kitchen")
        self.assertEqual(items["BBQ Chicken Thigh"], "hot_kitchen")
        self.assertEqual(items["Black Beans"], "cold_kitchen")
        self.assertEqual(items["Brulee Cheesecake"], "cold_kitchen")
        self.assertEqual(items["Chipotle Ranch & White Balsamic (Set on Tables)"], "cold_kitchen")
        self.assertEqual(items["Citrus Polla Asado, Chile Rellenos with Ranchero Sauce"], "hot_kitchen")
        self.assertEqual(items["Coffee Cake"], "cold_kitchen")
        self.assertEqual(items["Grilled Chicken Breast with Chimichurri Sauce, Cilantro Lime Rice, and Charro Beans (GF, DF)"], "hot_kitchen")
        self.assertEqual(items["Lemon Butter Asparagus"], "hot_kitchen")
        self.assertEqual(items["Mashed Potatoes"], "hot_kitchen")
        self.assertEqual(items["Pork Loin Marsala"], "hot_kitchen")
        self.assertEqual(items["Red Onion"], "cold_kitchen")
        self.assertEqual(items["Roasted Corn"], "cold_kitchen")
        self.assertEqual(items["Roasted Lemon with Thyme Chicken Breast"], "hot_kitchen")
        self.assertEqual(items["Scones"], "cold_kitchen")
        self.assertEqual(items["Strawberry Cheesecake - Preset"], "cold_kitchen")
        self.assertEqual(items["Sugar Biscuits"], "cold_kitchen")
        self.assertEqual(items["Tortilla Strips"], "cold_kitchen")

        remaining_item_names = [item["name"] for item in annotated[0]["items"]]
        self.assertNotIn("1 Decaf", remaining_item_names)
        self.assertNotIn("1 Tea", remaining_item_names)
        self.assertNotIn("1) Cucumber Mint Cooler - Lemonade", remaining_item_names)
        self.assertNotIn("10 In Back", remaining_item_names)
        self.assertNotIn("Comp Snacks for Up to 10 Staff Members", remaining_item_names)
        self.assertNotIn("Decaf Coffee (Group Providing Own Coffee Sleeves- No Starbucks Branding)", remaining_item_names)
        self.assertNotIn("Honey Syrup and Sparking Water", remaining_item_names)
        self.assertNotIn("Rotating", remaining_item_names)
        self.assertNotIn("The Uptown (Small Group Pricing) TBD- Plated Instead?", remaining_item_names)
        self.assertNotIn("Yellow Tables on Diagram NOT Pre-set", remaining_item_names)
        self.assertEqual(annotated[0]["operational_split"]["unknown_items"], [])

    def test_routes_yogurt_parfait_bar_structure_to_cold(self) -> None:
        sections = [
            {
                "title": "Yogurt Parfait Bar",
                "type": "course",
                "service_role": "other",
                "course_type": "other",
                "items": [
                    {"name": "Greek Yogurt", "source_text": "Greek Yogurt & Vanilla Yogurt"},
                    {"name": "Vanilla Yogurt", "source_text": "Greek Yogurt & Vanilla Yogurt"},
                    {"name": "Blueberries", "source_text": "Blueberries and Strawberries"},
                    {"name": "Strawberries", "source_text": "Blueberries and Strawberries"},
                    {"name": "Raw Honeycomb", "source_text": "Raw Honeycomb, Organic Granola, Sliced Almonds, Chia Seeds"},
                    {"name": "Organic Granola", "source_text": "Raw Honeycomb, Organic Granola, Sliced Almonds, Chia Seeds"},
                    {"name": "Sliced Almonds", "source_text": "Raw Honeycomb, Organic Granola, Sliced Almonds, Chia Seeds"},
                    {"name": "Chia Seeds", "source_text": "Raw Honeycomb, Organic Granola, Sliced Almonds, Chia Seeds"},
                ],
            }
        ]
        annotated = annotate_menu_sections_with_production(sections)
        items = {item["name"]: item["production_area"]["temperature_zone"] for item in annotated[0]["items"]}
        self.assertEqual(items["Greek Yogurt"], "cold_kitchen")
        self.assertEqual(items["Vanilla Yogurt"], "cold_kitchen")
        self.assertEqual(items["Blueberries"], "cold_kitchen")
        self.assertEqual(items["Strawberries"], "cold_kitchen")
        self.assertEqual(items["Raw Honeycomb"], "cold_kitchen")
        self.assertEqual(items["Organic Granola"], "cold_kitchen")
        self.assertEqual(items["Sliced Almonds"], "cold_kitchen")
        self.assertEqual(items["Chia Seeds"], "cold_kitchen")
        self.assertEqual(annotated[0]["operational_split"]["unknown_items"], [])

    def test_routes_tea_thyme_menu_to_cold(self) -> None:
        sections = [
            {
                "title": "Tea Thyme",
                "type": "course",
                "service_role": "other",
                "course_type": "other",
                "items": [
                    {"name": "Egg Salad on Mini Croissant", "source_text": "Egg Salad on Mini Croissant"},
                    {"name": "Queen Elizabeth's Curried Chicken Salad on Brioche", "source_text": "Queen Elizabeth's Curried Chicken Salad on Brioche"},
                    {"name": "Cold Smoked Sockeye Salmon", "source_text": "Cold Smoked Sockeye Salmon, Herb & Garlic Boursin, Bagel Crisp"},
                    {"name": "Garlic Boursin", "source_text": "Cold Smoked Sockeye Salmon, Herb & Garlic Boursin, Bagel Crisp"},
                    {"name": "Bagel Crisp", "source_text": "Cold Smoked Sockeye Salmon, Herb & Garlic Boursin, Bagel Crisp"},
                    {"name": "Assorted Scones", "source_text": "Assorted Scones"},
                    {"name": "Macarons - Assorted Flavors", "source_text": "Macarons - Assorted Flavors"},
                    {"name": "Petite Four Mini Desserts", "source_text": "Petite Four Mini Desserts"},
                    {"name": "Chocolate Dipped Strawberries", "source_text": "Chocolate Dipped Strawberries"},
                ],
            }
        ]
        annotated = annotate_menu_sections_with_production(sections)
        items = {item["name"]: item["production_area"]["temperature_zone"] for item in annotated[0]["items"]}
        self.assertEqual(items["Egg Salad on Mini Croissant"], "cold_kitchen")
        self.assertEqual(items["Queen Elizabeth's Curried Chicken Salad on Brioche"], "cold_kitchen")
        self.assertEqual(items["Cold Smoked Sockeye Salmon"], "cold_kitchen")
        self.assertEqual(items["Garlic Boursin"], "cold_kitchen")
        self.assertEqual(items["Bagel Crisp"], "cold_kitchen")
        self.assertEqual(items["Assorted Scones"], "cold_kitchen")
        self.assertEqual(items["Macarons - Assorted Flavors"], "cold_kitchen")
        self.assertEqual(items["Petite Four Mini Desserts"], "cold_kitchen")
        self.assertEqual(items["Chocolate Dipped Strawberries"], "cold_kitchen")
        self.assertEqual(annotated[0]["operational_split"]["unknown_items"], [])

    def test_routes_modified_pasta_station_and_mason_jar_caesar(self) -> None:
        sections = [
            {
                "title": "(Modified) Pasta Station",
                "type": "station_items",
                "service_role": "other",
                "course_type": "other",
                "items": [
                    {"name": "Cavatappi Carbonara- Chicken", "source_text": "Cavatappi Carbonara- Chicken , Wild Mushroom, Black Pepper, Parmesan"},
                    {"name": "Wild Mushroom", "source_text": "Cavatappi Carbonara- Chicken , Wild Mushroom, Black Pepper, Parmesan"},
                    {"name": "Parmesan", "source_text": "Cavatappi Carbonara- Chicken , Wild Mushroom, Black Pepper, Parmesan"},
                    {"name": "Vegetarian Penne a la Vodka- Grilled Chicken", "source_text": "Vegetarian Penne a la Vodka- Grilled Chicken, Roasted Peppers, Squash, Spinach"},
                    {"name": "Roasted Peppers", "source_text": "Vegetarian Penne a la Vodka- Grilled Chicken, Roasted Peppers, Squash, Spinach"},
                    {"name": "Squash", "source_text": "Vegetarian Penne a la Vodka- Grilled Chicken, Roasted Peppers, Squash, Spinach"},
                    {"name": "Spinach", "source_text": "Vegetarian Penne a la Vodka- Grilled Chicken, Roasted Peppers, Squash, Spinach"},
                    {"name": "Toppings", "source_text": "Toppings-"},
                    {"name": "Crushed Pepper", "source_text": "Crushed Pepper, Shredded Parmesan"},
                    {"name": "Shredded Parmesan", "source_text": "Crushed Pepper, Shredded Parmesan"},
                    {"name": "Micro Basil", "source_text": "Micro Basil, Crispy Onions"},
                    {"name": "Crispy Onions", "source_text": "Micro Basil, Crispy Onions"},
                    {"name": "Based on 60 Minutes of Continuous Service", "source_text": "Based on 60 Minutes of Continuous Service"},
                    {"name": "$34.00 per Person", "source_text": "$34.00 per Person"},
                ],
            },
            {
                "title": "Items",
                "type": "course",
                "service_role": "other",
                "course_type": "other",
                "items": [
                    {"name": "(75) Mason Jar Caesar @ $10 Each", "source_text": "(75) Mason Jar Caesar @ $10 Each"},
                    {"name": "Baby Gem", "source_text": "Baby Gem, Parmesan, Roasted Tomato, Garlic Croutons, Caesar Dressing"},
                    {"name": "Parmesan", "source_text": "Baby Gem, Parmesan, Roasted Tomato, Garlic Croutons, Caesar Dressing"},
                    {"name": "Roasted Tomato", "source_text": "Baby Gem, Parmesan, Roasted Tomato, Garlic Croutons, Caesar Dressing"},
                    {"name": "Garlic Croutons", "source_text": "Baby Gem, Parmesan, Roasted Tomato, Garlic Croutons, Caesar Dressing"},
                    {"name": "Caesar Dressing", "source_text": "Baby Gem, Parmesan, Roasted Tomato, Garlic Croutons, Caesar Dressing"},
                ],
            },
        ]

        annotated = annotate_menu_sections_with_production(sections)

        pasta_items = {item["name"]: item["production_area"]["temperature_zone"] for item in annotated[0]["items"]}
        self.assertEqual(pasta_items["Cavatappi Carbonara- Chicken"], "hot_kitchen")
        self.assertEqual(pasta_items["Wild Mushroom"], "hot_kitchen")
        self.assertEqual(pasta_items["Parmesan"], "cold_kitchen")
        self.assertEqual(pasta_items["Vegetarian Penne a la Vodka- Grilled Chicken"], "hot_kitchen")
        self.assertEqual(pasta_items["Roasted Peppers"], "hot_kitchen")
        self.assertEqual(pasta_items["Squash"], "hot_kitchen")
        self.assertEqual(pasta_items["Spinach"], "hot_kitchen")
        self.assertEqual(pasta_items["Shredded Parmesan"], "cold_kitchen")
        self.assertEqual(pasta_items["Micro Basil"], "cold_kitchen")
        self.assertEqual(pasta_items["Crispy Onions"], "cold_kitchen")
        pasta_remaining = [item["name"] for item in annotated[0]["items"]]
        self.assertNotIn("Toppings", pasta_remaining)
        self.assertNotIn("Crushed Pepper", pasta_remaining)
        self.assertNotIn("Based on 60 Minutes of Continuous Service", pasta_remaining)
        self.assertNotIn("$34.00 per Person", pasta_remaining)
        self.assertEqual(annotated[0]["operational_split"]["unknown_items"], [])

        caesar_items = {item["name"]: item["production_area"]["temperature_zone"] for item in annotated[1]["items"]}
        self.assertEqual(caesar_items["(75) Mason Jar Caesar @ $10 Each"], "cold_kitchen")
        self.assertEqual(caesar_items["Baby Gem"], "cold_kitchen")
        self.assertEqual(caesar_items["Parmesan"], "cold_kitchen")
        self.assertEqual(caesar_items["Roasted Tomato"], "cold_kitchen")
        self.assertEqual(caesar_items["Garlic Croutons"], "cold_kitchen")
        self.assertEqual(caesar_items["Caesar Dressing"], "cold_kitchen")
        self.assertEqual(annotated[1]["operational_split"]["unknown_items"], [])

    def test_routes_seafood_display_menu_to_cold(self) -> None:
        sections = [
            {
                "title": "Seafood Display - Market Price",
                "type": "display",
                "service_role": "other",
                "course_type": "other",
                "items": [
                    {"name": "Shucked Oysters", "source_text": "Shucked Oysters"},
                    {"name": "Citrus Poached Gulf Shrimp", "source_text": "Citrus Poached Gulf Shrimp"},
                    {"name": "Bloody Mary Crab Claw Shooters", "source_text": "Bloody Mary Crab Claw Shooters"},
                    {"name": "Peruvian Scallop Crudo", "source_text": "Peruvian Scallop Crudo"},
                    {"name": "Cocktail Sauce", "source_text": "Cocktail Sauce & Horseradish"},
                    {"name": "Horseradish", "source_text": "Cocktail Sauce & Horseradish"},
                    {"name": "Mignonette", "source_text": "Mignonette & Lemon Wedges"},
                    {"name": "Lemon Wedges", "source_text": "Mignonette & Lemon Wedges"},
                    {"name": "Horseradish and Lemon Wedges", "source_text": "Horseradish and Lemon Wedges"},
                ],
            }
        ]

        annotated = annotate_menu_sections_with_production(sections)
        items = {item["name"]: item["production_area"]["temperature_zone"] for item in annotated[0]["items"]}
        self.assertEqual(items["Shucked Oysters"], "cold_kitchen")
        self.assertEqual(items["Citrus Poached Gulf Shrimp"], "cold_kitchen")
        self.assertEqual(items["Bloody Mary Crab Claw Shooters"], "cold_kitchen")
        self.assertEqual(items["Peruvian Scallop Crudo"], "cold_kitchen")
        self.assertEqual(items["Cocktail Sauce"], "cold_kitchen")
        self.assertEqual(items["Horseradish"], "cold_kitchen")
        self.assertEqual(items["Mignonette"], "cold_kitchen")
        self.assertEqual(items["Lemon Wedges"], "cold_kitchen")
        self.assertEqual(items["Horseradish and Lemon Wedges"], "cold_kitchen")
        self.assertEqual(annotated[0]["operational_split"]["unknown_items"], [])

    def test_routes_mac_n_cheese_bar_menu(self) -> None:
        sections = [
            {
                "title": "(200) Mac n' Cheese Bar",
                "type": "station_items",
                "service_role": "other",
                "course_type": "other",
                "items": [
                    {"name": "Grilled Chicken", "source_text": "Grilled Chicken, Brisket Burnt Ends, Bacon Lardons"},
                    {"name": "Brisket Burnt Ends", "source_text": "Grilled Chicken, Brisket Burnt Ends, Bacon Lardons"},
                    {"name": "Bacon Lardons", "source_text": "Grilled Chicken, Brisket Burnt Ends, Bacon Lardons"},
                    {"name": "Grilled Wild Mushrooms", "source_text": "Grilled Wild Mushrooms, Butter Cracker Crumbs, Chives & Roasted Tomato, Parmesan Cheese, Gorgonzola Crumbles"},
                    {"name": "Butter Cracker Crumbs", "source_text": "Grilled Wild Mushrooms, Butter Cracker Crumbs, Chives & Roasted Tomato, Parmesan Cheese, Gorgonzola Crumbles"},
                    {"name": "Chives", "source_text": "Grilled Wild Mushrooms, Butter Cracker Crumbs, Chives & Roasted Tomato, Parmesan Cheese, Gorgonzola Crumbles"},
                    {"name": "Roasted Tomato", "source_text": "Grilled Wild Mushrooms, Butter Cracker Crumbs, Chives & Roasted Tomato, Parmesan Cheese, Gorgonzola Crumbles"},
                    {"name": "Parmesan Cheese", "source_text": "Grilled Wild Mushrooms, Butter Cracker Crumbs, Chives & Roasted Tomato, Parmesan Cheese, Gorgonzola Crumbles"},
                    {"name": "Gorgonzola Crumbles", "source_text": "Grilled Wild Mushrooms, Butter Cracker Crumbs, Chives & Roasted Tomato, Parmesan Cheese, Gorgonzola Crumbles"},
                ],
            }
        ]

        annotated = annotate_menu_sections_with_production(sections)
        items = {item["name"]: item["production_area"]["temperature_zone"] for item in annotated[0]["items"]}
        self.assertEqual(items["Grilled Chicken"], "hot_kitchen")
        self.assertEqual(items["Brisket Burnt Ends"], "hot_kitchen")
        self.assertEqual(items["Bacon Lardons"], "hot_kitchen")
        self.assertEqual(items["Grilled Wild Mushrooms"], "hot_kitchen")
        self.assertEqual(items["Butter Cracker Crumbs"], "cold_kitchen")
        self.assertEqual(items["Chives"], "cold_kitchen")
        self.assertEqual(items["Roasted Tomato"], "cold_kitchen")
        self.assertEqual(items["Parmesan Cheese"], "cold_kitchen")
        self.assertEqual(items["Gorgonzola Crumbles"], "cold_kitchen")
        self.assertEqual(annotated[0]["operational_split"]["unknown_items"], [])

    def test_routes_prime_rib_carving_station_menu(self) -> None:
        sections = [
            {
                "title": "(3) Herb Crusted Prime Rib Carving Station",
                "type": "station_items",
                "service_role": "other",
                "course_type": "other",
                "items": [
                    {"name": "Rosemary Au Jus", "source_text": "Rosemary Au Jus, Creamed Horseradish, Silver Dollar Rolls"},
                    {"name": "Creamed Horseradish", "source_text": "Rosemary Au Jus, Creamed Horseradish, Silver Dollar Rolls"},
                    {"name": "Silver Dollar Rolls", "source_text": "Rosemary Au Jus, Creamed Horseradish, Silver Dollar Rolls"},
                    {"name": "Requires Chef Attendant", "source_text": "Requires Chef Attendant"},
                ],
            }
        ]

        annotated = annotate_menu_sections_with_production(sections)
        items = {item["name"]: item["production_area"]["temperature_zone"] for item in annotated[0]["items"]}
        self.assertEqual(items["Rosemary Au Jus"], "hot_kitchen")
        self.assertEqual(items["Creamed Horseradish"], "cold_kitchen")
        self.assertEqual(items["Silver Dollar Rolls"], "hot_kitchen")
        remaining_item_names = [item["name"] for item in annotated[0]["items"]]
        self.assertNotIn("Requires Chef Attendant", remaining_item_names)
        self.assertEqual(annotated[0]["operational_split"]["unknown_items"], [])

    def test_routes_everyday_is_a_sundae_menu_to_cold(self) -> None:
        sections = [
            {
                "title": "Everyday is a Sundae",
                "type": "course",
                "service_role": "other",
                "course_type": "other",
                "items": [
                    {"name": "Chocolate Ice Cream", "source_text": "Chocolate & Vanilla Ice Cream"},
                    {"name": "Vanilla Ice Cream", "source_text": "Chocolate & Vanilla Ice Cream"},
                    {
                        "name": "Oreo Cookie",
                        "source_text": "Oreo Cookie, Cherries, Whipped Cream, Crushed Peanuts, Caramel Topping, Strawberry Topping, Chocolate Topping, Sprinkles",
                    },
                    {
                        "name": "Cherries",
                        "source_text": "Oreo Cookie, Cherries, Whipped Cream, Crushed Peanuts, Caramel Topping, Strawberry Topping, Chocolate Topping, Sprinkles",
                    },
                    {
                        "name": "Whipped Cream",
                        "source_text": "Oreo Cookie, Cherries, Whipped Cream, Crushed Peanuts, Caramel Topping, Strawberry Topping, Chocolate Topping, Sprinkles",
                    },
                    {
                        "name": "Crushed Peanuts",
                        "source_text": "Oreo Cookie, Cherries, Whipped Cream, Crushed Peanuts, Caramel Topping, Strawberry Topping, Chocolate Topping, Sprinkles",
                    },
                    {
                        "name": "Caramel Topping",
                        "source_text": "Oreo Cookie, Cherries, Whipped Cream, Crushed Peanuts, Caramel Topping, Strawberry Topping, Chocolate Topping, Sprinkles",
                    },
                    {
                        "name": "Strawberry Topping",
                        "source_text": "Oreo Cookie, Cherries, Whipped Cream, Crushed Peanuts, Caramel Topping, Strawberry Topping, Chocolate Topping, Sprinkles",
                    },
                    {
                        "name": "Chocolate Topping",
                        "source_text": "Oreo Cookie, Cherries, Whipped Cream, Crushed Peanuts, Caramel Topping, Strawberry Topping, Chocolate Topping, Sprinkles",
                    },
                    {
                        "name": "Sprinkles",
                        "source_text": "Oreo Cookie, Cherries, Whipped Cream, Crushed Peanuts, Caramel Topping, Strawberry Topping, Chocolate Topping, Sprinkles",
                    },
                ],
            }
        ]

        annotated = annotate_menu_sections_with_production(sections)
        items = {item["name"]: item["production_area"]["temperature_zone"] for item in annotated[0]["items"]}
        self.assertEqual(items["Chocolate Ice Cream"], "cold_kitchen")
        self.assertEqual(items["Vanilla Ice Cream"], "cold_kitchen")
        self.assertEqual(items["Oreo Cookie"], "cold_kitchen")
        self.assertEqual(items["Cherries"], "cold_kitchen")
        self.assertEqual(items["Whipped Cream"], "cold_kitchen")
        self.assertEqual(items["Crushed Peanuts"], "cold_kitchen")
        self.assertEqual(items["Caramel Topping"], "cold_kitchen")
        self.assertEqual(items["Strawberry Topping"], "cold_kitchen")
        self.assertEqual(items["Chocolate Topping"], "cold_kitchen")
        self.assertEqual(items["Sprinkles"], "cold_kitchen")
        self.assertEqual(annotated[0]["operational_split"]["unknown_items"], [])

    def test_routes_everyday_is_a_sundae_when_parser_keeps_items_under_generic_section(self) -> None:
        sections = [
            {
                "title": "Items",
                "type": "course",
                "service_role": "other",
                "course_type": "other",
                "items": [
                    {"name": "Everyday is a Sundae", "source_text": "Everyday is a Sundae"},
                    {"name": "Chocolate", "source_text": "Chocolate & Vanilla Ice Cream"},
                    {"name": "Vanilla Ice Cream", "source_text": "Chocolate & Vanilla Ice Cream"},
                    {
                        "name": "Oreo Cookie",
                        "source_text": "Oreo Cookie, Cherries, Whipped Cream, Crushed Peanuts, Caramel Topping, Strawberry Topping, Chocolate Topping, Sprinkles",
                    },
                    {
                        "name": "Cherries",
                        "source_text": "Oreo Cookie, Cherries, Whipped Cream, Crushed Peanuts, Caramel Topping, Strawberry Topping, Chocolate Topping, Sprinkles",
                    },
                    {
                        "name": "Crushed Peanuts",
                        "source_text": "Oreo Cookie, Cherries, Whipped Cream, Crushed Peanuts, Caramel Topping, Strawberry Topping, Chocolate Topping, Sprinkles",
                    },
                    {
                        "name": "Caramel Topping",
                        "source_text": "Oreo Cookie, Cherries, Whipped Cream, Crushed Peanuts, Caramel Topping, Strawberry Topping, Chocolate Topping, Sprinkles",
                    },
                    {
                        "name": "Strawberry Topping",
                        "source_text": "Oreo Cookie, Cherries, Whipped Cream, Crushed Peanuts, Caramel Topping, Strawberry Topping, Chocolate Topping, Sprinkles",
                    },
                    {
                        "name": "Chocolate Topping",
                        "source_text": "Oreo Cookie, Cherries, Whipped Cream, Crushed Peanuts, Caramel Topping, Strawberry Topping, Chocolate Topping, Sprinkles",
                    },
                    {
                        "name": "Sprinkles",
                        "source_text": "Oreo Cookie, Cherries, Whipped Cream, Crushed Peanuts, Caramel Topping, Strawberry Topping, Chocolate Topping, Sprinkles",
                    },
                ],
            }
        ]

        annotated = annotate_menu_sections_with_production(sections)
        items = {item["name"]: item["production_area"]["temperature_zone"] for item in annotated[0]["items"]}
        self.assertEqual(items["Everyday is a Sundae"], "cold_kitchen")
        self.assertEqual(items["Chocolate"], "cold_kitchen")
        self.assertEqual(items["Vanilla Ice Cream"], "cold_kitchen")
        self.assertEqual(items["Oreo Cookie"], "cold_kitchen")
        self.assertEqual(items["Cherries"], "cold_kitchen")
        self.assertEqual(items["Crushed Peanuts"], "cold_kitchen")
        self.assertEqual(items["Caramel Topping"], "cold_kitchen")
        self.assertEqual(items["Strawberry Topping"], "cold_kitchen")
        self.assertEqual(items["Chocolate Topping"], "cold_kitchen")
        self.assertEqual(items["Sprinkles"], "cold_kitchen")
        self.assertEqual(annotated[0]["operational_split"]["unknown_items"], [])

    def test_routes_finzly_revised_unknown_items(self) -> None:
        sections = [
            {
                "title": "Items",
                "type": "course",
                "service_role": "other",
                "course_type": "other",
                "items": [
                    {"name": "Farm Eggs", "source_text": "Farm Eggs"},
                ],
            },
            {
                "title": "(Modified) Pasta Station",
                "type": "station_items",
                "service_role": "other",
                "course_type": "other",
                "items": [
                    {"name": "Marinara Sauce", "source_text": "Marinara Sauce, Crushed Pepper, Shredded Parmesan"},
                    {"name": "Vegetarian Penne a la Vodka Roasted Peppers", "source_text": "Vegetarian Penne a la Vodka Roasted Peppers, Squash, Spinach"},
                ],
            },
        ]

        annotated = annotate_menu_sections_with_production(sections)
        breakfast_items = {item["name"]: item["production_area"]["temperature_zone"] for item in annotated[0]["items"]}
        self.assertEqual(breakfast_items["Farm Eggs"], "hot_kitchen")
        pasta_items = {item["name"]: item["production_area"]["temperature_zone"] for item in annotated[1]["items"]}
        self.assertEqual(pasta_items["Marinara Sauce"], "hot_kitchen")
        self.assertEqual(pasta_items["Vegetarian Penne a la Vodka Roasted Peppers"], "hot_kitchen")
        self.assertEqual(annotated[0]["operational_split"]["unknown_items"], [])
        self.assertEqual(annotated[1]["operational_split"]["unknown_items"], [])

    def test_routes_may_24_unknown_review_batch_without_unknowns(self) -> None:
        sections = [
            {
                "title": "Plated Dinner",
                "type": "course",
                "service_role": "other",
                "course_type": "other",
                "items": [
                    {"name": "1 Dairy Free dessert", "source_text": "1 Dairy Free dessert"},
                    {"name": "Apple Pie - NO PECANS", "source_text": "Apple Pie - NO PECANS"},
                    {"name": "Baby Spinach salad", "source_text": "Baby Spinach salad"},
                    {"name": "Brie Salad", "source_text": "Tomato & Brie Salad"},
                    {"name": "Garlic Chilli Broccolini", "source_text": "Garlic Chilli Broccolini"},
                    {"name": "Seared Salmon with Basil Pesto", "source_text": "Seared Salmon with Basil Pesto"},
                    {"name": "Sweet Pea Risotto", "source_text": "Sweet Pea Risotto"},
                    {"name": "Whipped Potatoes", "source_text": "Whipped Potatoes"},
                ],
            },
            {
                "title": "Hot Plated Lunch",
                "type": "course",
                "service_role": "other",
                "course_type": "other",
                "items": [
                    {"name": "Arugula/ Frisee Salad w White Balsamic Dressing", "source_text": "Arugula/ Frisee Salad w White Balsamic Dressing"},
                    {"name": "Fresh Fruit", "source_text": "Fresh Fruit"},
                    {"name": "Roasted Airline Chicken w/ Mushroom Farro", "source_text": "Roasted Airline Chicken w/ Mushroom Farro, Broccolini, Lemon Thyme Jus"},
                ],
            },
            {
                "title": "Items",
                "type": "course",
                "service_role": "other",
                "course_type": "other",
                "items": [
                    {"name": "Cauliflower Puree", "source_text": "Cauliflower Puree, Mushroom Farotto, Broccolini, Lemon Thyme Jus"},
                    {"name": "Client bringing in cake - no fee", "source_text": "Client bringing in cake - no fee"},
                    {"name": "FOOD Food Served from 12:00 PM - 1:00 PM", "source_text": "FOOD Food Served from 12:00 PM - 1:00 PM"},
                    {"name": "House Wine Glass", "source_text": "House Wine Glass @ $14 Each"},
                    {"name": "Iced Tea and Water at Each Place Setting", "source_text": "Iced Tea and Water at Each Place Setting"},
                    {"name": "Mushroom Farotto", "source_text": "Cauliflower Puree, Mushroom Farotto, Broccolini, Lemon Thyme Jus"},
                    {"name": "PRESET Chef's Choice Dessert", "source_text": "PRESET Chef's Choice Dessert"},
                    {"name": "Pinot Noir", "source_text": "Red, White, Rose, Sauvignon Blanc, Pinot Noir & Sparkling"},
                    {"name": "Premium Brands", "source_text": "Premium Brands @ $13 Each"},
                    {"name": "Registration Open from 4:00 PM - 6:00 PM.", "source_text": "Registration Open from 4:00 PM - 6:00 PM."},
                    {"name": "Sauvignon Blanc", "source_text": "Red, White, Rose, Sauvignon Blanc, Pinot Noir & Sparkling"},
                    {"name": "Selection of Rolls", "source_text": "Selection of Rolls & Butter"},
                    {"name": "Service 12:30pm-1:30pm", "source_text": "Service 12:30pm-1:30pm, leave out additional 30 minutes until 2pm"},
                    {"name": "Sparkling", "source_text": "Red, White, Rose, Sauvignon Blanc, Pinot Noir & Sparkling"},
                    {"name": "Sparkling Wine", "source_text": "Red, White, Rose, Sauvignon Blanc, Pinot Noir, Sparkling Wine"},
                    {"name": "Tableside Starbucks Coffee Service", "source_text": "Tableside Starbucks Coffee Service"},
                    {"name": "leave out additional 30 minutes until 2pm", "source_text": "Service 12:30pm-1:30pm, leave out additional 30 minutes until 2pm"},
                ],
            },
        ]

        annotated = annotate_menu_sections_with_production(sections)

        dinner_items = {item["name"]: item["production_area"]["temperature_zone"] for item in annotated[0]["items"]}
        self.assertEqual(dinner_items["1 Dairy Free dessert"], "dietary")
        self.assertEqual(dinner_items["Apple Pie - NO PECANS"], "dietary")
        self.assertEqual(dinner_items["Baby Spinach salad"], "cold_kitchen")
        self.assertEqual(dinner_items["Brie Salad"], "cold_kitchen")
        self.assertEqual(dinner_items["Garlic Chilli Broccolini"], "hot_kitchen")
        self.assertEqual(dinner_items["Seared Salmon with Basil Pesto"], "hot_kitchen")
        self.assertEqual(dinner_items["Sweet Pea Risotto"], "hot_kitchen")
        self.assertEqual(dinner_items["Whipped Potatoes"], "hot_kitchen")

        lunch_items = {item["name"]: item["production_area"]["temperature_zone"] for item in annotated[1]["items"]}
        self.assertEqual(lunch_items["Arugula/ Frisee Salad w White Balsamic Dressing"], "cold_kitchen")
        self.assertEqual(lunch_items["Fresh Fruit"], "cold_kitchen")
        self.assertEqual(lunch_items["Roasted Airline Chicken w/ Mushroom Farro"], "hot_kitchen")

        items = {item["name"]: item["production_area"]["temperature_zone"] for item in annotated[2]["items"]}
        self.assertEqual(items["Cauliflower Puree"], "hot_kitchen")
        self.assertEqual(items["Mushroom Farotto"], "hot_kitchen")
        self.assertEqual(items["PRESET Chef's Choice Dessert"], "cold_kitchen")
        self.assertEqual(items["Selection of Rolls"], "hot_kitchen")
        self.assertEqual(items["House Wine Glass"], "unknown")
        self.assertEqual(items["Pinot Noir"], "unknown")
        self.assertEqual(items["Premium Brands"], "unknown")
        self.assertEqual(items["Sauvignon Blanc"], "unknown")
        self.assertEqual(items["Sparkling"], "unknown")
        self.assertEqual(items["Sparkling Wine"], "unknown")
        remaining_item_names = [item["name"] for item in annotated[2]["items"]]
        self.assertNotIn("Client bringing in cake - no fee", remaining_item_names)
        self.assertNotIn("FOOD Food Served from 12:00 PM - 1:00 PM", remaining_item_names)
        self.assertNotIn("Iced Tea and Water at Each Place Setting", remaining_item_names)
        self.assertNotIn("Registration Open from 4:00 PM - 6:00 PM.", remaining_item_names)
        self.assertNotIn("Service 12:30pm-1:30pm", remaining_item_names)
        self.assertNotIn("Tableside Starbucks Coffee Service", remaining_item_names)
        self.assertNotIn("leave out additional 30 minutes until 2pm", remaining_item_names)

        for section in annotated:
            self.assertEqual(section["operational_split"]["unknown_items"], [])

    def test_routes_full_passed_lines_with_markdown_markers(self) -> None:
        sections = [
            {
                "title": "Items",
                "type": "course",
                "service_role": "other",
                "course_type": "other",
                "items": [
                    {
                        "name": "(150) Crispy Vegetable Dumpling, Ponzu Sauce **PASSED* @ $6.5 Each",
                        "source_text": "(150) Crispy Vegetable Dumpling, Ponzu Sauce **PASSED* @ $6.5 Each",
                    },
                    {
                        "name": "(150) Peruvian Ceviche, Lime, Red Onion, Habanero **PASSED** @ $7 Each",
                        "source_text": "(150) Peruvian Ceviche, Lime, Red Onion, Habanero **PASSED** @ $7 Each",
                    },
                    {
                        "name": "(150) Herb Goat Cheese & Tomato Jam on Crostini **PASSED** @ $7 Each",
                        "source_text": "(150) Herb Goat Cheese & Tomato Jam on Crostini **PASSED** @ $7 Each",
                    },
                    {
                        "name": "(150) Beef Filet & Blue Cheese Wellington **PASSED** @ $8 Each",
                        "source_text": "(150) Beef Filet & Blue Cheese Wellington **PASSED** @ $8 Each",
                    },
                ],
            }
        ]

        annotated = annotate_menu_sections_with_production(sections)
        items = {item["name"]: item["production_area"]["temperature_zone"] for item in annotated[0]["items"]}
        self.assertEqual(items["(150) Crispy Vegetable Dumpling, Ponzu Sauce **PASSED* @ $6.5 Each"], "hot_kitchen")
        self.assertEqual(items["(150) Peruvian Ceviche, Lime, Red Onion, Habanero **PASSED** @ $7 Each"], "cold_kitchen")
        self.assertEqual(items["(150) Herb Goat Cheese & Tomato Jam on Crostini **PASSED** @ $7 Each"], "cold_kitchen")
        self.assertEqual(items["(150) Beef Filet & Blue Cheese Wellington **PASSED** @ $8 Each"], "hot_kitchen")
        self.assertEqual(annotated[0]["operational_split"]["unknown_items"], [])

    def test_routes_smoothie_bar_menu_headers_and_component_lines_to_cold(self) -> None:
        sections = [
            {
                "title": "Items",
                "type": "course",
                "service_role": "other",
                "course_type": "other",
                "items": [
                    {"name": "Smoothie Bar", "source_text": "(5) Smoothie Bar @ $160 per Gallon"},
                    {"name": "THE MANGO PINEAPPLE", "source_text": "THE MANGO PINEAPPLE"},
                    {"name": "Mango", "source_text": "Mango, Pineapple, Coconut Water"},
                    {"name": "Pineapple", "source_text": "Mango, Pineapple, Coconut Water"},
                    {"name": "Coconut Water", "source_text": "Mango, Pineapple, Coconut Water"},
                    {"name": "THE BANANA STRAWBERRY", "source_text": "THE BANANA STRAWBERRY"},
                    {"name": "Banana", "source_text": "Banana, Strawberry, Vanilla Yogurt"},
                    {"name": "Strawberry", "source_text": "Banana, Strawberry, Vanilla Yogurt"},
                    {"name": "Vanilla Yogurt", "source_text": "Banana, Strawberry, Vanilla Yogurt"},
                    {"name": "THE MIXED BERRY", "source_text": "THE MIXED BERRY"},
                    {"name": "Mixed Berries", "source_text": "Mixed Berries, Agave"},
                    {"name": "Agave", "source_text": "Mixed Berries, Agave"},
                ],
            }
        ]

        annotated = annotate_menu_sections_with_production(sections)
        items = {item["name"]: item["production_area"]["temperature_zone"] for item in annotated[0]["items"]}
        self.assertEqual(items["Smoothie Bar"], "cold_kitchen")
        self.assertEqual(items["THE MANGO PINEAPPLE"], "cold_kitchen")
        self.assertEqual(items["Mango"], "cold_kitchen")
        self.assertEqual(items["Pineapple"], "cold_kitchen")
        self.assertEqual(items["Coconut Water"], "cold_kitchen")
        self.assertEqual(items["THE BANANA STRAWBERRY"], "cold_kitchen")
        self.assertEqual(items["Banana"], "cold_kitchen")
        self.assertEqual(items["Strawberry"], "cold_kitchen")
        self.assertEqual(items["Vanilla Yogurt"], "cold_kitchen")
        self.assertEqual(items["THE MIXED BERRY"], "cold_kitchen")
        self.assertEqual(items["Mixed Berries"], "cold_kitchen")
        self.assertEqual(items["Agave"], "cold_kitchen")
        self.assertEqual(annotated[0]["operational_split"]["unknown_items"], [])

    def test_routes_may_17_unknown_review_batch_without_unknowns(self) -> None:
        sections = [
            {
                "title": "Items",
                "type": "course",
                "service_role": "other",
                "course_type": "other",
                "items": [
                    {"name": "(6) Starbucks Regular Coffee", "source_text": "(6) (6) Starbucks Regular Coffee"},
                    {"name": "1 Celiac", "source_text": "1 Celiac"},
                    {"name": "Ask before refresh", "source_text": "Ask before refresh"},
                    {"name": "Assorted Bagels with Butter and Whipped Cream Cheese", "source_text": "(3) Assorted Bagels with Butter and Whipped Cream Cheese @ $48 per Dozen"},
                    {"name": "Assorted Clif Protein Bars", "source_text": "(20) Assorted Clif Protein Bars @ $7 Each"},
                    {"name": "Banana", "source_text": "Banana, Strawberry, Vanilla Yogurt"},
                    {"name": "Agave", "source_text": "Mixed Berries, Agave"},
                    {"name": "Decaffeinated Coffee", "source_text": "(2) Decaffeinated Coffee, Assorted Tazo Teas and Condiments @ $105 per Gallon"},
                    {"name": "Farm Eggs OR Egg Whites", "source_text": "Farm Eggs OR Egg Whites"},
                    {"name": "Granola Bars", "source_text": "(1) Granola Bars @ $6 Each"},
                    {"name": "Green Beans", "source_text": "(125) Green Beans @ $6"},
                    {"name": "Individual Greek Yogurt Parfaits with Fresh Berries & Granola", "source_text": "(35) Individual Greek Yogurt Parfaits with Fresh Berries & Granola @ $9 Each"},
                    {"name": "Peruvian Ceviche", "source_text": "(150) Peruvian Ceviche, Lime, Red Onion, Habanero PASSED @ $7 Each"},
                    {"name": "Lime", "source_text": "(150) Peruvian Ceviche, Lime, Red Onion, Habanero PASSED @ $7 Each"},
                    {"name": "Habanero PASSED", "source_text": "(150) Peruvian Ceviche, Lime, Red Onion, Habanero PASSED @ $7 Each"},
                    {"name": "Herb Goat Cheese", "source_text": "(150) Herb Goat Cheese & Tomato Jam on Crostini PASSED @ $7 Each"},
                    {"name": "Tomato Jam on Crostini PASSED", "source_text": "(150) Herb Goat Cheese & Tomato Jam on Crostini PASSED @ $7 Each"},
                    {"name": "(150) Beef Filet & Blue Cheese Wellington PASSED @ $8 Each", "source_text": "(150) Beef Filet & Blue Cheese Wellington PASSED @ $8 Each"},
                    {"name": "Blue Cheese Wellington PASSED", "source_text": "(150) Beef Filet & Blue Cheese Wellington PASSED @ $8 Each"},
                    {"name": "Crisp Lemongrass Chicken Dumpling with Sweet Thai Sauce PASSED", "source_text": "(150) Crisp Lemongrass Chicken Dumpling with Sweet Thai Sauce PASSED @ $6.5 Each"},
                    {"name": "Crispy Shrimp Dumpling with Lime Soy Sauce PASSED", "source_text": "(150) Crispy Shrimp Dumpling with Lime Soy Sauce PASSED @ $6.5 Each"},
                    {"name": "Ponzu Sauce PASSED*", "source_text": "(150) Crispy Vegetable Dumpling, Ponzu Sauce PASSED* @ $6.5 Each"},
                ],
            },
            {
                "title": "Seafood Display - Market Price",
                "type": "display",
                "service_role": "other",
                "course_type": "other",
                "items": [
                    {"name": "Bloody Mary Crab Claw Shooters", "source_text": "Bloody Mary Crab Claw Shooters"},
                    {"name": "Citrus Poached Gulf Shrimp", "source_text": "Citrus Poached Gulf Shrimp"},
                    {"name": "Cocktail Sauce", "source_text": "Cocktail Sauce & Horseradish"},
                    {"name": "Horseradish", "source_text": "Cocktail Sauce & Horseradish"},
                    {"name": "Horseradish and Lemon Wedges", "source_text": "Horseradish and Lemon Wedges"},
                    {"name": "House Champagne", "source_text": "(5) House Champagne @ $53 per Bottle"},
                    {"name": "Lemon Wedges", "source_text": "Mignonette & Lemon Wedges"},
                    {"name": "Mignonette", "source_text": "Mignonette & Lemon Wedges"},
                    {"name": "On Consumption per bottle", "source_text": "On Consumption per bottle"},
                    {"name": "Only served for the first hour", "source_text": "Only served for the first hour"},
                    {"name": "Peruvian Scallop Crudo", "source_text": "Peruvian Scallop Crudo"},
                    {"name": "Shucked Oysters", "source_text": "Shucked Oysters"},
                ],
            },
            {
                "title": "(200) Shrimp & Grits Station",
                "type": "station_items",
                "service_role": "other",
                "course_type": "other",
                "items": [
                    {"name": "Smoked Cheddar Grits", "source_text": "Smoked Cheddar Grits, Blackened Shrimp, Spicy Andouille Sausage"},
                    {"name": "Blackened Shrimp", "source_text": "Smoked Cheddar Grits, Blackened Shrimp, Spicy Andouille Sausage"},
                    {"name": "Spicy Andouille Sausage", "source_text": "Smoked Cheddar Grits, Blackened Shrimp, Spicy Andouille Sausage"},
                    {"name": "Roasted Pepper", "source_text": "Roasted Pepper, Micro Cilantro, Bacon Lardons, Grilled Wild Mushroom"},
                    {"name": "Micro Cilantro", "source_text": "Roasted Pepper, Micro Cilantro, Bacon Lardons, Grilled Wild Mushroom"},
                    {"name": "Grilled Wild Mushroom", "source_text": "Roasted Pepper, Micro Cilantro, Bacon Lardons, Grilled Wild Mushroom"},
                ],
            },
            {
                "title": "(200) Mac n' Cheese Bar",
                "type": "station_items",
                "service_role": "other",
                "course_type": "other",
                "items": [
                    {"name": "Butter Cracker Crumbs", "source_text": "Grilled Wild Mushrooms, Butter Cracker Crumbs, Chives & Roasted Tomato, Parmesan Cheese, Gorgonzola Crumbles"},
                    {"name": "Chives", "source_text": "Grilled Wild Mushrooms, Butter Cracker Crumbs, Chives & Roasted Tomato, Parmesan Cheese, Gorgonzola Crumbles"},
                    {"name": "Gorgonzola Crumbles", "source_text": "Grilled Wild Mushrooms, Butter Cracker Crumbs, Chives & Roasted Tomato, Parmesan Cheese, Gorgonzola Crumbles"},
                    {"name": "Parmesan Cheese", "source_text": "Grilled Wild Mushrooms, Butter Cracker Crumbs, Chives & Roasted Tomato, Parmesan Cheese, Gorgonzola Crumbles"},
                ],
            },
            {
                "title": "(Modified) Pasta Station",
                "type": "station_items",
                "service_role": "other",
                "course_type": "other",
                "items": [
                    {"name": "Black Pepper", "source_text": "Cavatappi Carbonara- Chicken , Wild Mushroom, Black Pepper, Parmesan"},
                    {"name": "Cavatappi Carbonara- Chicken", "source_text": "Cavatappi Carbonara- Chicken , Wild Mushroom, Black Pepper, Parmesan"},
                    {"name": "Crushed Pepper", "source_text": "Crushed Pepper, Shredded Parmesan"},
                    {"name": "Crispy Onions", "source_text": "Micro Basil, Crispy Onions"},
                    {"name": "Micro Basil", "source_text": "Micro Basil, Crispy Onions"},
                    {"name": "Roasted Peppers", "source_text": "Vegetarian Penne a la Vodka- Grilled Chicken, Roasted Peppers, Squash, Spinach"},
                    {"name": "Shredded Parmesan", "source_text": "Crushed Pepper, Shredded Parmesan"},
                    {"name": "Spinach", "source_text": "Vegetarian Penne a la Vodka- Grilled Chicken, Roasted Peppers, Squash, Spinach"},
                    {"name": "Squash", "source_text": "Vegetarian Penne a la Vodka- Grilled Chicken, Roasted Peppers, Squash, Spinach"},
                    {"name": "Toppings", "source_text": "Toppings-"},
                    {"name": "Vegetarian Penne a la Vodka- Grilled Chicken", "source_text": "Vegetarian Penne a la Vodka- Grilled Chicken, Roasted Peppers, Squash, Spinach"},
                    {"name": "Wild Mushroom", "source_text": "Cavatappi Carbonara- Chicken , Wild Mushroom, Black Pepper, Parmesan"},
                ],
            },
            {
                "title": "(200) Fajita Station",
                "type": "station_items",
                "service_role": "other",
                "course_type": "other",
                "items": [
                    {"name": "Choose One Protein", "source_text": "Choose One Protein"},
                    {"name": "Choose 2: Tomatoes", "source_text": "Choose 2: Tomatoes, Peppers,"},
                    {"name": "Peppers", "source_text": "Choose 2: Tomatoes, Peppers,"},
                    {"name": "Grilled Peppers", "source_text": "Grilled Peppers & Onions Sour Cream, Tomato Salsa, Cheddar Cheese, Guacamole"},
                    {"name": "Guacamole", "source_text": "Grilled Peppers & Onions Sour Cream, Tomato Salsa, Cheddar Cheese, Guacamole"},
                    {"name": "Onions Sour Cream", "source_text": "Grilled Peppers & Onions Sour Cream, Tomato Salsa, Cheddar Cheese, Guacamole"},
                    {"name": "Tomato Salsa", "source_text": "Grilled Peppers & Onions Sour Cream, Tomato Salsa, Cheddar Cheese, Guacamole"},
                ],
            },
            {
                "title": "(3) Herb Crusted Prime Rib Carving Station",
                "type": "station_items",
                "service_role": "other",
                "course_type": "other",
                "items": [
                    {"name": "Creamed Horseradish", "source_text": "Rosemary Au Jus, Creamed Horseradish, Silver Dollar Rolls"},
                    {"name": "Requires Chef Attendant", "source_text": "Requires Chef Attendant"},
                    {"name": "Rosemary Au Jus", "source_text": "Rosemary Au Jus, Creamed Horseradish, Silver Dollar Rolls"},
                    {"name": "Silver Dollar Rolls", "source_text": "Rosemary Au Jus, Creamed Horseradish, Silver Dollar Rolls"},
                ],
            },
            {
                "title": "Deluxe Host Brands",
                "type": "course",
                "service_role": "other",
                "course_type": "other",
                "items": [
                    {"name": "Casamigos Silver Tequila", "source_text": "Casamigos Silver Tequila"},
                    {"name": "Craft", "source_text": "Sierra Nevada Hazy IPA, Craft, Chico"},
                    {"name": "Crown Royal Canadian Whiskey", "source_text": "Crown Royal Canadian Whiskey"},
                    {"name": "Cruzan Rum", "source_text": "Cruzan Rum"},
                    {"name": "Grey Goose Vodka", "source_text": "Grey Goose Vodka"},
                    {"name": "Johnnie Walker Black Scotch", "source_text": "Johnnie Walker Black Scotch"},
                    {"name": "Premium", "source_text": "Stella Artois, Premium, Belgium"},
                    {"name": "Selection of Deluxe Wines", "source_text": "Selection of Deluxe Wines @ $14 Each"},
                    {"name": "Tanqueray Gin", "source_text": "Tanqueray Gin"},
                    {"name": "Woodford Reserve Kentucky Bourbon", "source_text": "Woodford Reserve Kentucky Bourbon"},
                ],
            },
        ]

        annotated = annotate_menu_sections_with_production(sections)

        items_section = {item["name"]: item["production_area"]["temperature_zone"] for item in annotated[0]["items"]}
        self.assertEqual(items_section["Assorted Bagels with Butter and Whipped Cream Cheese"], "cold_kitchen")
        self.assertEqual(items_section["Assorted Clif Protein Bars"], "cold_kitchen")
        self.assertEqual(items_section["Farm Eggs OR Egg Whites"], "hot_kitchen")
        self.assertEqual(items_section["Granola Bars"], "cold_kitchen")
        self.assertEqual(items_section["Green Beans"], "hot_kitchen")
        self.assertEqual(items_section["Individual Greek Yogurt Parfaits with Fresh Berries & Granola"], "cold_kitchen")
        self.assertEqual(items_section["Peruvian Ceviche"], "cold_kitchen")
        self.assertEqual(items_section["Lime"], "cold_kitchen")
        self.assertEqual(items_section["Habanero PASSED"], "cold_kitchen")
        self.assertEqual(items_section["Herb Goat Cheese"], "cold_kitchen")
        self.assertEqual(items_section["Tomato Jam on Crostini PASSED"], "cold_kitchen")
        self.assertEqual(items_section["(150) Beef Filet & Blue Cheese Wellington PASSED @ $8 Each"], "hot_kitchen")
        self.assertEqual(items_section["Blue Cheese Wellington PASSED"], "hot_kitchen")
        self.assertEqual(items_section["Crisp Lemongrass Chicken Dumpling with Sweet Thai Sauce PASSED"], "hot_kitchen")
        self.assertEqual(items_section["Crispy Shrimp Dumpling with Lime Soy Sauce PASSED"], "hot_kitchen")
        self.assertEqual(items_section["Ponzu Sauce PASSED*"], "hot_kitchen")
        self.assertEqual(items_section["1 Celiac"], "dietary")
        self.assertEqual(items_section["Banana"], "cold_kitchen")
        self.assertEqual(items_section["Agave"], "cold_kitchen")
        remaining_item_names = [item["name"] for item in annotated[0]["items"]]
        self.assertNotIn("(6) Starbucks Regular Coffee", remaining_item_names)
        self.assertNotIn("Ask before refresh", remaining_item_names)
        self.assertNotIn("Decaffeinated Coffee", remaining_item_names)

        seafood_items = {item["name"]: item["production_area"]["temperature_zone"] for item in annotated[1]["items"]}
        self.assertEqual(seafood_items["Bloody Mary Crab Claw Shooters"], "cold_kitchen")
        self.assertEqual(seafood_items["Citrus Poached Gulf Shrimp"], "cold_kitchen")
        self.assertEqual(seafood_items["Cocktail Sauce"], "cold_kitchen")
        self.assertEqual(seafood_items["Horseradish"], "cold_kitchen")
        self.assertEqual(seafood_items["Horseradish and Lemon Wedges"], "cold_kitchen")
        self.assertEqual(seafood_items["Lemon Wedges"], "cold_kitchen")
        self.assertEqual(seafood_items["Mignonette"], "cold_kitchen")
        self.assertEqual(seafood_items["Peruvian Scallop Crudo"], "cold_kitchen")
        self.assertEqual(seafood_items["Shucked Oysters"], "cold_kitchen")
        self.assertEqual(seafood_items["House Champagne"], "unknown")
        seafood_remaining = [item["name"] for item in annotated[1]["items"]]
        self.assertNotIn("On Consumption per bottle", seafood_remaining)
        self.assertNotIn("Only served for the first hour", seafood_remaining)

        shrimp_grits_items = {item["name"]: item["production_area"]["temperature_zone"] for item in annotated[2]["items"]}
        self.assertEqual(shrimp_grits_items["Smoked Cheddar Grits"], "hot_kitchen")
        self.assertEqual(shrimp_grits_items["Blackened Shrimp"], "hot_kitchen")
        self.assertEqual(shrimp_grits_items["Spicy Andouille Sausage"], "hot_kitchen")
        self.assertEqual(shrimp_grits_items["Roasted Pepper"], "hot_kitchen")
        self.assertEqual(shrimp_grits_items["Micro Cilantro"], "hot_kitchen")
        self.assertEqual(shrimp_grits_items["Grilled Wild Mushroom"], "hot_kitchen")

        mac_items = {item["name"]: item["production_area"]["temperature_zone"] for item in annotated[3]["items"]}
        self.assertEqual(mac_items["Butter Cracker Crumbs"], "cold_kitchen")
        self.assertEqual(mac_items["Chives"], "cold_kitchen")
        self.assertEqual(mac_items["Gorgonzola Crumbles"], "cold_kitchen")
        self.assertEqual(mac_items["Parmesan Cheese"], "cold_kitchen")

        pasta_items = {item["name"]: item["production_area"]["temperature_zone"] for item in annotated[4]["items"]}
        self.assertEqual(pasta_items["Cavatappi Carbonara- Chicken"], "hot_kitchen")
        self.assertEqual(pasta_items["Crispy Onions"], "cold_kitchen")
        self.assertEqual(pasta_items["Micro Basil"], "cold_kitchen")
        self.assertEqual(pasta_items["Roasted Peppers"], "hot_kitchen")
        self.assertEqual(pasta_items["Shredded Parmesan"], "cold_kitchen")
        self.assertEqual(pasta_items["Spinach"], "hot_kitchen")
        self.assertEqual(pasta_items["Squash"], "hot_kitchen")
        self.assertEqual(pasta_items["Vegetarian Penne a la Vodka- Grilled Chicken"], "hot_kitchen")
        self.assertEqual(pasta_items["Wild Mushroom"], "hot_kitchen")
        pasta_remaining = [item["name"] for item in annotated[4]["items"]]
        self.assertNotIn("Black Pepper", pasta_remaining)
        self.assertNotIn("Crushed Pepper", pasta_remaining)
        self.assertNotIn("Toppings", pasta_remaining)

        fajita_items = {item["name"]: item["production_area"]["temperature_zone"] for item in annotated[5]["items"]}
        self.assertEqual(fajita_items["Grilled Peppers"], "hot_kitchen")
        self.assertEqual(fajita_items["Guacamole"], "cold_kitchen")
        self.assertEqual(fajita_items["Tomato Salsa"], "cold_kitchen")
        fajita_remaining = [item["name"] for item in annotated[5]["items"]]
        self.assertNotIn("Choose One Protein", fajita_remaining)
        self.assertNotIn("Choose 2: Tomatoes", fajita_remaining)
        self.assertNotIn("Peppers", fajita_remaining)
        self.assertNotIn("Onions Sour Cream", fajita_remaining)

        carving_items = {item["name"]: item["production_area"]["temperature_zone"] for item in annotated[6]["items"]}
        self.assertEqual(carving_items["Creamed Horseradish"], "cold_kitchen")
        self.assertEqual(carving_items["Rosemary Au Jus"], "hot_kitchen")
        self.assertEqual(carving_items["Silver Dollar Rolls"], "hot_kitchen")
        carving_remaining = [item["name"] for item in annotated[6]["items"]]
        self.assertNotIn("Requires Chef Attendant", carving_remaining)

        deluxe_items = {item["name"]: item["production_area"]["temperature_zone"] for item in annotated[7]["items"]}
        self.assertEqual(deluxe_items["Casamigos Silver Tequila"], "unknown")
        self.assertEqual(deluxe_items["Crown Royal Canadian Whiskey"], "unknown")
        self.assertEqual(deluxe_items["Cruzan Rum"], "unknown")
        self.assertEqual(deluxe_items["Grey Goose Vodka"], "unknown")
        self.assertEqual(deluxe_items["Johnnie Walker Black Scotch"], "unknown")
        self.assertEqual(deluxe_items["Selection of Deluxe Wines"], "unknown")
        self.assertEqual(deluxe_items["Tanqueray Gin"], "unknown")
        self.assertEqual(deluxe_items["Woodford Reserve Kentucky Bourbon"], "unknown")
        deluxe_remaining = [item["name"] for item in annotated[7]["items"]]
        self.assertNotIn("Craft", deluxe_remaining)
        self.assertNotIn("Premium", deluxe_remaining)

        for section in annotated:
            self.assertEqual(section["operational_split"]["unknown_items"], [])


if __name__ == "__main__":
    unittest.main()
