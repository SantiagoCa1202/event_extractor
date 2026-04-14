from __future__ import annotations

from copy import deepcopy


HOT_ITEM_RULES = {
    "assorted rolls with butter": "exact_item_rule",
    "rolls with butter": "exact_item_rule",
    "roasted airline chicken breast with herb roasted potatoes, broccolini, and lemon thyme jus": "exact_item_rule",
    "curry roasted cauliflower": "exact_item_rule",
    "garlic mashed potatoes": "exact_item_rule",
    "sauteed green beans": "exact_item_rule",
    "ground beef": "exact_item_rule",
    "nacho cheese": "exact_item_rule",
    "steel cut oatmeal": "exact_item_rule",
    "oatmeal": "exact_item_rule",
    "croissant sandwich - smoked ham, egg patty, american cheese": "exact_item_rule",
    "biscuit sandwich - smoked bacon, egg patty, american cheese": "exact_item_rule",
    "bagel sandwich - pork sage sausage, egg patty, cheddar cheese": "exact_item_rule",
    "english muffin - turkey sausage, egg patty, american cheese": "exact_item_rule",
    "breakfast burritos": "exact_item_rule",
    "scrambled eggs": "exact_item_rule",
    "bacon": "exact_item_rule",
    "grilled chicken": "exact_item_rule",
    "brisket burnt ends": "exact_item_rule",
    "bacon lardons": "exact_item_rule",
    "grilled wild mushrooms": "exact_item_rule",
    "roasted airline chicken breast": "exact_item_rule",
    "roasted lemon thyme chicken breast": "exact_item_rule",
    "steak medallions with red wine reduction": "exact_item_rule",
    "seared salmon with a cajun cream sauce": "exact_item_rule",
    "herbs de provence pork loin": "exact_item_rule",
    "applewood smoked thick cut bacon": "exact_item_rule",
    "rosemary roasted potatoes": "exact_item_rule",
    "chicken apple sausage (1 pc)": "exact_item_rule",
    "locally sourced krispy kreme original glaze donuts": "exact_item_rule",
    "badass bobs pretzels with whole grain mustard": "exact_item_rule",
    "mini corndogs": "exact_item_rule",
    "baked egg casserole": "exact_item_rule",
    "hashbrown": "exact_item_rule",
    "chicken sausage": "exact_item_rule",
    "chicken picatta": "exact_item_rule",
    "meatball marinara": "exact_item_rule",
    "vegetable lasagna": "exact_item_rule",
    "penne pasta with butter and parsley": "exact_item_rule",
    "garlic & chili broccolini": "exact_item_rule",
    "north carolina smoked pulled pork": "exact_item_rule",
    "smoked brisket": "exact_item_rule",
    "bbq rub shrimp": "exact_item_rule",
    "bbq baked beans": "exact_item_rule",
    "egg white florentine": "exact_item_rule",
    "potatoes o'brien": "exact_item_rule",
    "sweet rolls with butter": "exact_item_rule",
    "east bbq": "exact_item_rule",
    "sweet bbq": "exact_item_rule",
    "creamy mac & cheese": "exact_item_rule",
    "tortilla chips": "exact_item_rule",
    "flank steak with chimichurri": "exact_item_rule",
    "citrus pollo asado": "exact_item_rule",
    "cilantro lime rice": "exact_item_rule",
    "charros beans": "exact_item_rule",
    "entree choice:beef short ribs and seared scallops": "exact_item_rule",
    "pancakes with butter and syrup": "exact_item_rule",
    "cauliflower": "exact_item_rule",
    "caluiflower": "exact_item_rule",
    "applewood smoked thick cut bacon/chicken apple sausage (half and half)": "exact_item_rule",
    "stuffed mushrooms": "exact_item_rule",
    "shrimp cocktail (4 pieces of shrimp per order)": "exact_item_rule",
    "beef filet": "exact_item_rule",
    "blue cheese wellington": "exact_item_rule",
    "bacon wrapped scallops": "exact_item_rule",
    "ring dinner bell": "exact_item_rule",
    "roast lamb loin": "exact_item_rule",
    "macaroni & cheese bites": "exact_item_rule",
    "cheesesteak spring rolls": "exact_item_rule",
    "self-serve chicken wings": "exact_item_rule",
    "bbq": "exact_item_rule",
    "korean": "exact_item_rule",
    "buffalo sauce on side": "exact_item_rule",
}

HOT_ITEM_KEYWORD_RULES = {
    "beef tenderloin": "keyword_item_rule:beef_tenderloin",
    "roasted salmon": "keyword_item_rule:roasted_salmon",
}

NON_KITCHEN_ITEM_RULES = {
    "premium brand cocktails": "beverage_item_rule",
    "tito's vodka": "beverage_item_rule",
    "beefeater gin": "beverage_item_rule",
    "bacardi superior rum": "beverage_item_rule",
    "captain morgan original spiced rum": "beverage_item_rule",
    "patron silver tequila": "beverage_item_rule",
    "jack daniels tennessee whiskey": "beverage_item_rule",
    "makers mark kentucky bourbon": "beverage_item_rule",
    "dewar's white label scotch": "beverage_item_rule",
    "hennessy vs cognac": "beverage_item_rule",
    "selection of premium wines by the glass": "beverage_item_rule",
    "red": "beverage_item_rule",
    "white": "beverage_item_rule",
    "rose": "beverage_item_rule",
    "specialty beer": "beverage_item_rule",
    "stella artois": "beverage_item_rule",
    "sierra nevada hazy ipa": "beverage_item_rule",
    "local craft": "beverage_item_rule",
    "domestic beer host": "beverage_item_rule",
    "yuengling": "beverage_item_rule",
    "bud light": "beverage_item_rule",
    "michelob ultra": "beverage_item_rule",
    "hard seltzer": "beverage_item_rule",
    "assorted pepsi sodas": "beverage_item_rule",
    "assorted pepsi products": "beverage_item_rule",
    "assorted teavana teas": "beverage_item_rule",
    "bottled water": "beverage_item_rule",
    "bottled waters": "beverage_item_rule",
    "fresh fruit juices": "beverage_item_rule",
}

COLD_ITEM_RULES = {
    "assorted sliced cake": "exact_item_rule",
    "spring mix": "exact_item_rule",
    "cherry tomato": "exact_item_rule",
    "cucumber": "exact_item_rule",
    "shredded carrot": "exact_item_rule",
    "shredded cheddar": "exact_item_rule",
    "black olives": "exact_item_rule",
    "buttermilk ranch": "exact_item_rule",
    "white balsamic dressing": "exact_item_rule",
    "lemon bars": "exact_item_rule",
    "assorted pastries": "exact_item_rule",
    "assorted whole fruit": "exact_item_rule",
    "brie": "exact_item_rule",
    "gorgonzola": "exact_item_rule",
    "manchego": "exact_item_rule",
    "grapes": "exact_item_rule",
    "berries": "exact_item_rule",
    "seasonal jam": "exact_item_rule",
    "assorted crackers and toast points": "exact_item_rule",
    "dried apricot": "exact_item_rule",
    "marcona almonds": "exact_item_rule",
    "baby carrots": "exact_item_rule",
    "baby spinach": "exact_item_rule",
    "celery": "exact_item_rule",
    "sweet peppers": "exact_item_rule",
    "asparagus": "exact_item_rule",
    "broccolini": "exact_item_rule",
    "buttermilk herb dip": "exact_item_rule",
    "pickled jalapenos": "exact_item_rule",
    "tomatoes": "exact_item_rule",
    "green onion": "exact_item_rule",
    "sour cream": "exact_item_rule",
    "corn relish": "exact_item_rule",
    "dairy": "exact_item_rule",
    "non dairy add-ins": "exact_item_rule",
    "fresh sliced fruit": "exact_item_rule",
    "individual yogurts": "exact_item_rule",
    "assorted granola bars": "exact_item_rule",
    "assorted miss vicky kettle chips": "exact_item_rule",
    "assorted full-size candy bars": "exact_item_rule",
    "assorted protein bars": "exact_item_rule",
    "assorted danish": "exact_item_rule",
    "croissants": "exact_item_rule",
    "biscuits": "exact_item_rule",
    "strawberry": "exact_item_rule",
    "apricot jam": "exact_item_rule",
    "golden raisins": "exact_item_rule",
    "golden raises": "exact_item_rule",
    "sliced almonds": "exact_item_rule",
    "brown sugar": "exact_item_rule",
    "chips": "exact_item_rule",
    "pretzels": "exact_item_rule",
    "rold gold mini pretzel": "exact_item_rule",
    "popcorn": "exact_item_rule",
    "assorted granola": "exact_item_rule",
    "protein and breakfast bars": "exact_item_rule",
    "assorted granola and protein/power bars": "exact_item_rule",
    "queen city pimento cheese": "exact_item_rule",
    "butter cracker": "exact_item_rule",
    "mixed candy": "exact_item_rule",
    "romaine": "exact_item_rule",
    "cherry tomato": "exact_item_rule",
    "carrot": "exact_item_rule",
    "parmesan": "exact_item_rule",
    "croutons": "exact_item_rule",
    "caesar dressing": "exact_item_rule",
    "coleslaw": "exact_item_rule",
    "pickle chips": "exact_item_rule",
    "pico de gallo": "exact_item_rule",
    "crema": "exact_item_rule",
    "cured meat and cheeses": "exact_item_rule",
    "pickled vegetables": "exact_item_rule",
    "crackers": "exact_item_rule",
    "accoutrement": "exact_item_rule",
    "individual yogurt": "exact_item_rule",
    "smartfood popcorn": "exact_item_rule",
    "fresh jumbo cookies": "exact_item_rule",
    "artisan lettuce salad, dried cherries, goat cheese, spiced candied walnuts, champagne vinaigrette": "exact_item_rule",
    "hazel nut crunch cake": "exact_item_rule",
    "brule cheesecake": "exact_item_rule",
    "baby spinach with cherry tomato": "exact_item_rule",
    "fresh whole fruit": "exact_item_rule",
    "queen city pimento cheese with butter cracker": "exact_item_rule",
    "cheddar": "exact_item_rule",
    "tomato crostini": "exact_item_rule",
    "ranch": "exact_item_rule",
    "buttermilk ranch dressing": "exact_item_rule",
    "blue cheese on side": "exact_item_rule",
}

COLD_ITEM_KEYWORD_RULES = {
    "brownie": "keyword_item_rule:brownie",
    "brownies": "keyword_item_rule:brownie",
}

HOT_CONTEXT_RULES = {
    ("nacho display", "tortilla chips"): "section_context_rule:nacho_display",
}

COLD_CONTEXT_RULES = {
    ("continental", "danish"): "section_context_rule:continental_breakfast",
    ("continental", "croissants"): "section_context_rule:continental_breakfast",
    ("continental", "mini biscuits"): "section_context_rule:continental_breakfast",
    ("continental", "strawberry"): "section_context_rule:continental_breakfast",
    ("continental", "apricot jam"): "section_context_rule:continental_breakfast",
    ("continental", "assorted cereals"): "section_context_rule:continental_breakfast",
}

COLD_SECTION_TYPES = {"cold_items", "snack_items", "salad_items"}
HOT_SECTION_TYPES = {"hot_items"}
NON_KITCHEN_SECTION_TYPES = {"beverage", "break_items"}
COURSE_TYPE_ROUTES = {
    "salad": ("cold_kitchen", "medium", "course_type_rule:salad"),
    "entree": ("hot_kitchen", "medium", "course_type_rule:entree"),
    "dessert": ("cold_kitchen", "medium", "course_type_rule:dessert"),
}
IGNORED_ITEM_RULES = {
    "soft drinks and bottled water",
    "complimentary per contract",
    "available upon request",
    "cheerwine soda",
    "breaks in foyer",
    "breaks on foyer",
    "start with 250. ask contact before refresh",
    "start with 60 gallons. ask contact to before refresh",
    "start with 250. ask before refresh",
    "and a selection of hot tazo teas",
    "assorted pepsi soft drinks",
    "lemonade",
    "decoration provided by extravaganza events - set up to begin @ 3pm.",
    "iced tea",
    "two hours premium brands bar package",
    "house wine",
    "red wine",
    "rose wine",
    "white wine",
    "wine is only served upon request; do not pre-set tables with wine options.",
    "chef attendant (one per 75 guests)",
    "on consumption available 7am-5pm",
    "waters",
    "tractor organic artisan ice tea",
    "open symphony ballroom doors at 6:15pm",
    "food 5:00 pm-6:15 pm reception symphony convention foyer",
    "(3) bars to serve liquor only",
    "(2) bars to serve beer",
    "wine only",
    "no tequila to be served at bars",
    "client request -- no shots or straight liquor",
    "must serve mixed",
    "drinks only",
    "after dinner",
    "group to visit tannin & toast from 7:00 am - 7:30 am",
}


def annotate_menu_sections_with_production(menu_sections: list[dict]) -> list[dict]:
    annotated = deepcopy(menu_sections)
    for section in annotated:
        filtered_items = []
        hot_items: list[str] = []
        cold_items: list[str] = []
        unknown_items: list[str] = []
        for item in section.get("items", []):
            production_area = _classify_item(section, item)
            if production_area["reason"] == "ignored_item_rule":
                continue
            item["production_area"] = production_area
            filtered_items.append(item)
            zone = production_area["temperature_zone"]
            if zone == "hot_kitchen":
                hot_items.append(item["name"])
            elif zone == "cold_kitchen":
                cold_items.append(item["name"])
            else:
                unknown_items.append(item["name"])
        section["items"] = filtered_items
        section["operational_split"] = {
            "hot_kitchen_items": hot_items,
            "cold_kitchen_items": cold_items,
            "unknown_items": unknown_items,
        }
    return annotated


def _classify_item(section: dict, item: dict) -> dict:
    item_name = (item.get("name") or "").strip().lower().rstrip(",")
    item_name = item_name.removeprefix("(passed) ").removeprefix("(displayed) ")
    section_title = (section.get("title") or "").strip().lower()
    section_type = (section.get("type") or "").strip().lower()
    course_type = (section.get("course_type") or "").strip().lower()

    if item_name in IGNORED_ITEM_RULES:
        return _build_production_area("ignored", "high", "ignored_item_rule")
    if (section_title, item_name) in HOT_CONTEXT_RULES:
        return _build_production_area("hot_kitchen", "medium", HOT_CONTEXT_RULES[(section_title, item_name)])
    if (section_title, item_name) in COLD_CONTEXT_RULES:
        return _build_production_area("cold_kitchen", "medium", COLD_CONTEXT_RULES[(section_title, item_name)])
    if item_name in HOT_ITEM_RULES:
        return _build_production_area("hot_kitchen", "high", HOT_ITEM_RULES[item_name])

    matched_hot_keyword = next((reason for keyword, reason in HOT_ITEM_KEYWORD_RULES.items() if keyword in item_name), None)
    if matched_hot_keyword:
        return _build_production_area("hot_kitchen", "high", matched_hot_keyword)
    if item_name in NON_KITCHEN_ITEM_RULES:
        return _build_production_area("unknown", "high", NON_KITCHEN_ITEM_RULES[item_name])
    if item_name in COLD_ITEM_RULES:
        return _build_production_area("cold_kitchen", "high", COLD_ITEM_RULES[item_name])

    matched_cold_keyword = next((reason for keyword, reason in COLD_ITEM_KEYWORD_RULES.items() if keyword in item_name), None)
    if matched_cold_keyword:
        return _build_production_area("cold_kitchen", "high", matched_cold_keyword)
    if course_type in COURSE_TYPE_ROUTES:
        zone, confidence, reason = COURSE_TYPE_ROUTES[course_type]
        return _build_production_area(zone, confidence, reason)
    if section_type in HOT_SECTION_TYPES:
        return _build_production_area("hot_kitchen", "medium", f"section_type_rule:{section_type}")
    if section_type in NON_KITCHEN_SECTION_TYPES:
        return _build_production_area("unknown", "medium", f"section_type_rule:{section_type}")
    if section_type in COLD_SECTION_TYPES:
        return _build_production_area("cold_kitchen", "medium", f"section_type_rule:{section_type}")
    return _build_production_area("unknown", "low", "no_matching_rule")


def _build_production_area(zone: str, confidence: str, reason: str) -> dict:
    return {
        "temperature_zone": zone,
        "confidence": confidence,
        "reason": reason,
    }
