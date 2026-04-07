import unittest

from beo_pipeline.food_service_filter import is_food_service_function


class FoodServiceFilterTests(unittest.TestCase):
    def test_rejects_explicit_no_food_phrase(self) -> None:
        ok, reasons = is_food_service_function("Meeting", "No Food or Beverage Required at this Time")
        self.assertFalse(ok)
        self.assertTrue(reasons)

    def test_accepts_meeting_with_real_beverage_service(self) -> None:
        ok, reasons = is_food_service_function(
            "Meeting",
            "Full Day Beverage Break\nAssorted Pepsi Sodas\nFreshly Brewed Coffee\nBottled Water",
            menu_item_count=4,
        )
        self.assertTrue(ok)
        self.assertTrue(any("menu_items" in reason for reason in reasons))

    def test_rejects_water_station_and_soft_drinks_only(self) -> None:
        ok, reasons = is_food_service_function(
            "Meeting",
            "2:00 PM Meeting Cardinal Ballroom Foyer\n(25) Assorted Pepsi Products @ $4.5 Each\nWater Station",
            menu_item_count=1,
            item_names=["Assorted Pepsi Products"],
        )
        self.assertFalse(ok)
        self.assertIn("excluded_non_food_beverage_service", reasons)


if __name__ == "__main__":
    unittest.main()
