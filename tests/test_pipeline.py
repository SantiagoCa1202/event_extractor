import unittest

from beo_pipeline import extract_events_from_text_pages


PAGE_ONE = """EVENT ORDER Page # 1 of 2
SHERATON CHARLOTTE HOTEL Event Order #: 708398
FUNCTION DAY/DATE: Wednesday, April 08, 2026
ORGANIZATION: Maximo Utility Working Group
ATTENDANCE
TIME FUNCTION LOCATION ROOM RENTAL EXP GTD SET
7:00 AM-11:59 PM Registration Symphony Convention 1
Foyer
7:00 AM-8:30 AM Continental Breakfast Symphony Convention 400
Foyer
10:00 AM-10:45 AM Coffee Break Symphony Convention 400
Foyer
7:00 AM Continental Breakfast Symphony Convention Foyer
Continental
Danish, Croissants, Mini Biscuits
Strawberry + Apricot Jam
Assorted Cereals
Individual Yogurts
Fresh Sliced Fruit
Starbucks Regular & Decaf Coffee
Tea, Orange Juice
10:00 AM Coffee Break Symphony Convention Foyer
Starbucks Regular and Decaffeinated Coffee, Assorted Tazo Teas and Condiments @ $94.5 per Gallon
"""

PAGE_TWO = """EVENT ORDER Page # 2 of 2
SHERATON CHARLOTTE HOTEL Event Order #: 708398
FUNCTION DAY/DATE: Wednesday, April 08, 2026
ORGANIZATION: Maximo Utility Working Group
(15) Assorted Pastries @ $37.8 per Dozen
2:15 PM-2:45 PM Coffee Break Symphony Convention 400
Foyer
2:15 PM Coffee Break Symphony Convention Foyer
Starbucks Regular and Decaffeinated Coffee, Assorted Tazo Teas and Condiments @ $94.5 per Gallon
(25) Lemon Bars @ $50.4 per Dozen
ROOM SETUP 7:00 AM-11:59 PM Registration Symphony Convention Foyer
Registration
"""

NON_FOOD_PAGE = """EVENT ORDER Page # 1 of 1
SHERATON CHARLOTTE HOTEL Event Order #: 708272
FUNCTION DAY/DATE: Tuesday, April 07, 2026
ORGANIZATION: Maximo Utility Working Group
ATTENDANCE
TIME FUNCTION LOCATION ROOM RENTAL EXP GTD SET
8:00 AM-11:59 PM Set Up Symphony 1 60
POST AS: Breakout
5:00 PM-7:00 PM Registration Symphony Convention 1 Foyer
No Food or Beverage Required at this Time
ROOM SETUP 8:00 AM-11:59 PM Set Up Symphony 1
Schoolroom
"""


class PipelineTests(unittest.TestCase):
    def test_handles_multi_page_continuity_and_filters_non_food(self) -> None:
        events = extract_events_from_text_pages([PAGE_ONE, PAGE_TWO, NON_FOOD_PAGE])
        self.assertEqual(len(events), 3)
        breakfast = next(event for event in events if event["service"]["function"] == "Continental Breakfast")
        self.assertEqual(breakfast["service"]["meal_period"], "breakfast")
        self.assertEqual(breakfast["service"]["gtd"], 400)
        self.assertEqual(breakfast["source_trace"]["page_ranges"], ["1"])
        self.assertEqual(breakfast["timeline"]["setup"], "6:30 AM")
        self.assertEqual(breakfast["timeline"]["pickup_food"], "6:10 AM")
        self.assertEqual(breakfast["timeline"]["clean_up"], "9:10 AM")
        self.assertTrue(breakfast["setup"]["breakdown_station"]["required"])
        self.assertEqual(breakfast["setup"]["breakdown_station"]["quantity"], 2)
        self.assertEqual(breakfast["setup"]["breakdown_station"]["size"], "l")

        coffee_breaks = [event for event in events if event["service"]["category"] == "break"]
        self.assertEqual(len(coffee_breaks), 2)
        self.assertTrue(all("break" in event["tags"] for event in coffee_breaks))
        spanning_break = next(event for event in coffee_breaks if event["service"]["time"]["start"] == "10:00 AM")
        self.assertEqual(spanning_break["source_trace"]["page_ranges"], ["1-2"])
        self.assertEqual(spanning_break["timeline"]["setup"], "9:30 AM")
        self.assertEqual(spanning_break["timeline"]["pickup_food"], "9:10 AM")
        self.assertEqual(spanning_break["timeline"]["clean_up"], "11:25 AM")

    def test_omits_meeting_with_only_water_station_and_pepsi(self) -> None:
        pages = [
            """EVENT ORDER Page # 1 of 1
SHERATON CHARLOTTE HOTEL Event Order #: 708251
FUNCTION DAY/DATE: Monday, April 06, 2026
ORGANIZATION: Maximo Utility Working Group
ATTENDANCE
TIME FUNCTION LOCATION ROOM RENTAL EXP GTD SET
2:00 PM-5:00 PM Meeting Cardinal Ballroom Foyer 1 30
2:00 PM Meeting Cardinal Ballroom Foyer
(25) Assorted Pepsi Products @ $4.5 Each
Water Station
ROOM SETUP 2:00 PM-5:00 PM Meeting Cardinal Ballroom Foyer
U-Shape
"""
        ]
        events = extract_events_from_text_pages(pages)
        self.assertEqual(events, [])

    def test_omits_offsite_group_logistics_that_are_not_hotel_food_service(self) -> None:
        pages = [
            """EVENT ORDER Page # 1 of 1
SHERATON CHARLOTTE HOTEL Event Order #: 708999
FUNCTION DAY/DATE: Thursday, April 09, 2026
ORGANIZATION: Maximo Utility Working Group
ATTENDANCE
TIME FUNCTION LOCATION ROOM RENTAL EXP GTD SET
4:30 PM-5:45 PM Reception Lobby 30
4:30 PM Reception Lobby
Group to Visit Tannin & Toast from 4:30PM - 5:45PM
Group will order drinks & appetizers on own and will settle bill by credit card at event conclusion.
Group will have one tab for all guests
Group to go offsite for dinner at McNinch House
ROOM SETUP 4:30 PM-5:45 PM Reception Lobby
Cocktail
"""
        ]
        events = extract_events_from_text_pages(pages)
        self.assertEqual(events, [])

    def test_omits_city_lights_offsite_logistics_variant(self) -> None:
        pages = [
            """EVENT ORDER Page # 1 of 1
SHERATON CHARLOTTE HOTEL Event Order #: 709001
FUNCTION DAY/DATE: Thursday, April 16, 2026
ORGANIZATION: Example Group
ATTENDANCE
TIME FUNCTION LOCATION ROOM RENTAL EXP GTD SET
8:00 PM-12:00 AM Reception CCSC 60
8:00 PM Reception CCSC
Group to Visit City Lights from 8:00PM - 12:00AM - Please reserve semi-private space for the group.
Group will order drinks & appetizers on own and will setlle bill by credit card at event conclusion.
Group will have one tab for all guests
Should inclemement weather cause reception to be moved, please reserve a semi-private space at CCSC
ROOM SETUP 8:00 PM-12:00 AM Reception CCSC
Cocktail
"""
        ]
        events = extract_events_from_text_pages(pages)
        self.assertEqual(events, [])

    def test_builds_buffet_and_break_from_meeting_context(self) -> None:
        pages = [
            """EVENT ORDER Page # 1 of 2
SHERATON CHARLOTTE HOTEL Event Order #: 529069
FUNCTION DAY/DATE: Wednesday, April 08, 2026
ORGANIZATION: Siemens Healthineers
ATTENDANCE
TIME FUNCTION LOCATION ROOM RENTAL EXP GTD SET
9:00 AM-5:00 PM Meeting Executive Boardroom $750.00 12 12
9:00 AM-10:00 AM Breakfast Buffet Executive Boardroom 12
12:00 PM-1:00 PM Lunch Buffet Executive Boardroom 12
3:00 PM-4:00 PM Break Executive Boardroom 12
9:00 AM Meeting Executive Boardroom
Full Day Beverage Break
Assorted Pepsi Sodas
Freshly Brewed Starbucks Regular and Decaffeinated Coffee to Include Sweeteners, Dairy & Non Dairy Add-Ins
Bottled Water
9:00 AM Breakfast Buffet
Continental
Danish, Croissants, Mini Biscuits
12:00 PM Lunch Buffet
The Queens Table
Assorted Rolls with Butter
Choice of Two Proteins:
Roasted Lemon Thyme Chicken Breast
"""
        ]
        events = extract_events_from_text_pages(pages)
        self.assertEqual(len(events), 3)
        categories = {event["service"]["category"] for event in events}
        self.assertIn("buffet", categories)
        self.assertIn("break", categories)
        lunch_buffet = next(event for event in events if event["service"]["category"] == "buffet")
        self.assertFalse(lunch_buffet["setup"]["breakdown_station"]["required"])
        self.assertEqual(lunch_buffet["setup"]["breakdown_station"]["quantity"], 0)

    def test_plated_event_has_no_menu_style(self) -> None:
        pages = [
            """EVENT ORDER Page # 1 of 1
SHERATON CHARLOTTE HOTEL Event Order #: 708547
FUNCTION DAY/DATE: Wednesday, April 08, 2026
ORGANIZATION: Maximo Utility Working Group
ATTENDANCE
TIME FUNCTION LOCATION ROOM RENTAL EXP GTD SET
12:00 PM-1:00 PM Plated Lunch Carolina Ballroom 400
12:00 PM Plated Lunch Carolina Ballroom
Hot Plated Lunch
Mixed Greens- Cucumber, Radish, Tomatoes, Carrots, Ranch and Balsamic Vinaigrette on Table
Rolls with Butter
Roasted Airline Chicken Breast with Herb Roasted Potatoes, Broccolini, and Lemon Thyme Jus
Chef's Choice Dessert- Two Types at Alternative Place Settings
ROOM SETUP 12:00 PM-1:00 PM Plated Lunch Carolina Ballroom
Rounds of 10
"""
        ]
        events = extract_events_from_text_pages(pages)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["service"]["category"], "plated")
        self.assertIsNone(events[0]["service"]["menu_style"])
        self.assertEqual(events[0]["timeline"]["setup"], "11:30 AM")
        self.assertEqual(events[0]["timeline"]["pickup_food"], "11:10 AM")
        self.assertEqual(events[0]["timeline"]["clean_up"], "1:40 PM")
        self.assertTrue(events[0]["setup"]["breakdown_station"]["required"])
        self.assertEqual(events[0]["setup"]["breakdown_station"]["quantity"], 2)
        self.assertEqual(events[0]["setup"]["breakdown_station"]["size"], "l")

    def test_reception_keeps_undetailed_displays_and_stations(self) -> None:
        pages = [
            """EVENT ORDER Page # 1 of 1
SHERATON CHARLOTTE HOTEL Event Order #: 708600
FUNCTION DAY/DATE: Wednesday, April 08, 2026
ORGANIZATION: Maximo Utility Working Group
ATTENDANCE
TIME FUNCTION LOCATION ROOM RENTAL EXP GTD SET
5:00 PM-7:00 PM Reception Carolina Ballroom 250
5:00 PM Reception Carolina Ballroom
Cheese Display
Vegetable Display
Charcuterie Display
Pepper Crusted Tenderloin Carving Station
Turkey Breast Carving Station
Cedar Plank Salmon Carving Station
Mashed Potato Bar
ROOM SETUP 5:00 PM-7:00 PM Reception Carolina Ballroom
Rounds of 10
"""
        ]
        events = extract_events_from_text_pages(pages)
        self.assertEqual(len(events), 1)
        event = events[0]
        self.assertEqual(event["service"]["category"], "reception")
        self.assertEqual(
            [section["title"] for section in event["details"]["menu_sections"]],
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
            [section["type"] for section in event["details"]["menu_sections"]],
            ["display", "display", "display", "station_items", "station_items", "station_items", "station_items"],
        )
        self.assertTrue(all(section["items"] == [] for section in event["details"]["menu_sections"]))
        self.assertEqual(event["setup"]["breakdown_station"]["quantity"], 2)
        self.assertEqual(event["setup"]["breakdown_station"]["size"], "l")

    def test_events_under_25_guests_do_not_require_breakdown_station(self) -> None:
        pages = [
            """EVENT ORDER Page # 1 of 1
SHERATON CHARLOTTE HOTEL Event Order #: 708610
FUNCTION DAY/DATE: Wednesday, April 08, 2026
ORGANIZATION: Siemens Healthineers
ATTENDANCE
TIME FUNCTION LOCATION ROOM RENTAL EXP GTD SET
12:00 PM-1:00 PM Lunch Buffet Executive Boardroom 12
12:00 PM Lunch Buffet Executive Boardroom
The Queens Table
Assorted Rolls with Butter
ROOM SETUP 12:00 PM-1:00 PM Lunch Buffet Executive Boardroom
Boardroom
"""
        ]
        events = extract_events_from_text_pages(pages)
        self.assertEqual(len(events), 1)
        breakdown = events[0]["setup"]["breakdown_station"]
        self.assertFalse(breakdown["required"])
        self.assertEqual(breakdown["quantity"], 0)

    def test_parses_room_patterns_with_internal_exp_and_room_suffixes(self) -> None:
        pages = [
            """EVENT ORDER Page # 1 of 1
SHERATON CHARLOTTE HOTEL Event Order #: 709200
FUNCTION DAY/DATE: Wednesday, April 15, 2026
ORGANIZATION: Example Group
ATTENDANCE
TIME FUNCTION LOCATION ROOM RENTAL EXP GTD SET
7:00 AM-8:00 AM Breakfast Buffet Symphony 6 & 7 50 100
12:00 PM-1:00 PM Plated Lunch Carolina A & C 25 150
3:00 PM-4:00 PM Break Governor's 2 & 3 175
5:00 PM-6:00 PM Break Executive Boardroom 12 12
7:00 AM Breakfast Buffet Symphony 6 & 7
Continental
Danish
12:00 PM Plated Lunch Carolina A & C
Hot Plated Lunch
Chicken
3:00 PM Break Governor's 2 & 3
Coffee
5:00 PM Break Executive Boardroom
Coffee
ROOM SETUP 7:00 AM-8:00 AM Breakfast Buffet Symphony 6 & 7
"""
        ]
        events = extract_events_from_text_pages(pages)

        symphony = next(event for event in events if event["service"]["time"]["start"] == "7:00 AM")
        self.assertEqual(symphony["service"]["room"], "Symphony 6 & 7")
        self.assertEqual(symphony["service"]["gtd"], 50)

        carolina = next(event for event in events if event["service"]["time"]["start"] == "12:00 PM")
        self.assertEqual(carolina["service"]["room"], "Carolina A & C")
        self.assertEqual(carolina["service"]["gtd"], 25)

        governors = next(event for event in events if event["service"]["time"]["start"] == "3:00 PM")
        self.assertEqual(governors["service"]["room"], "Governor's 2 & 3")
        self.assertEqual(governors["service"]["gtd"], 175)

        executive = next(event for event in events if event["service"]["time"]["start"] == "5:00 PM")
        self.assertEqual(executive["service"]["room"], "Executive Boardroom")
        self.assertEqual(executive["service"]["gtd"], 12)


if __name__ == "__main__":
    unittest.main()
