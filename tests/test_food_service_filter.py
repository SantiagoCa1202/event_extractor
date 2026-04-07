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


if __name__ == "__main__":
    unittest.main()
