PAIRING_RULES: dict = {
    "steak": {
        "grapes": ["Cabernet Sauvignon", "Malbec", "Syrah"],
        "why": "Bold tannins cut through fat and protein richness",
    },
    "beef": {
        "grapes": ["Cabernet Sauvignon", "Malbec", "Tempranillo"],
        "why": "Full-bodied reds complement the richness of beef",
    },
    "lamb": {
        "grapes": ["Cabernet Sauvignon", "Syrah", "Nebbiolo"],
        "why": "Structured tannins and dark fruit pair well with lamb's gaminess",
    },
    "seafood": {
        "grapes": ["Sauvignon Blanc", "Chablis", "Albarino"],
        "why": "Crisp acidity complements delicate flavors without overpowering",
    },
    "sushi": {
        "grapes": ["Champagne", "Sauvignon Blanc", "Riesling"],
        "why": "Light, crisp wines match raw fish's delicacy; bubbles cleanse the palate",
    },
    "chicken": {
        "grapes": ["Chardonnay", "Pinot Noir", "Chenin Blanc"],
        "why": "Medium-bodied wines match chicken's versatile flavor",
    },
    "pork": {
        "grapes": ["Riesling", "Pinot Noir", "Grenache"],
        "why": "Fruity wines with moderate tannins complement pork's sweetness",
    },
    "pasta": {
        "grapes": ["Sangiovese", "Barbera", "Pinot Grigio"],
        "why": "Italian grapes naturally pair with Italian dishes; acidity cuts through sauce",
    },
    "cheese": {
        "grapes": ["Port", "Sauternes", "Riesling"],
        "why": "Sweet wines contrast salty cheese; also try bold reds with hard cheese",
    },
    "chocolate": {
        "grapes": ["Port", "Malbec", "Shiraz"],
        "why": "Rich, sweet, or fruit-forward wines complement chocolate's bitterness",
    },
    "spicy_food": {
        "grapes": ["Riesling", "Gewurztraminer", "Chenin Blanc"],
        "why": "Off-dry wines with residual sugar tame heat; low alcohol is key",
    },
    "salad": {
        "grapes": ["Sauvignon Blanc", "Pinot Grigio", "Vermentino"],
        "why": "Light, crisp whites match green salads without overwhelming them",
    },
    "business_dinner": {
        "tip": "Choose recognizable labels — Bordeaux and Burgundy signal sophistication. Stay mid-to-high budget. Avoid polarizing styles (orange wine, pét-nat). Safe bets: a good Bordeaux red or a Champagne to start.",
    },
    "romantic_dinner": {
        "tip": "Prioritize elegance over power. Burgundy Pinot Noir, a fine Champagne, or an aromatic Riesling create memorable moments. Rosé from Provence is also a crowd-pleaser.",
    },
    "casual_gathering": {
        "tip": "Value-driven crowd-pleasers work best. Argentine Malbec, Cotes du Rhone, or a crisp Sauvignon Blanc. Nothing too complex — the goal is easy enjoyment.",
    },
}

REGION_FACTS: dict[str, str] = {
    "Bordeaux": "Known for structured reds. Left bank = Cabernet Sauvignon dominant. Right bank = Merlot dominant. Classified growths date to 1855.",
    "Burgundy": "Home of Pinot Noir and Chardonnay. Terroir-driven, village-level classifications. Prices range from affordable Bourgogne to stratospheric Grand Cru.",
    "Champagne": "Only sparkling wine from this region can legally be called Champagne. Methode traditionelle with secondary fermentation in bottle.",
    "Loire": "France's garden — diverse styles from bone-dry Muscadet to honeyed Vouvray. Chenin Blanc and Sauvignon Blanc dominate.",
    "Rhone": "Northern Rhone = Syrah (Hermitage, Cote-Rotie). Southern Rhone = blends led by Grenache (Chateauneuf-du-Pape). Great value at Cotes du Rhone level.",
    "Alsace": "French region with Germanic influence. Known for aromatic whites — Riesling, Gewurztraminer, Pinot Gris. Mostly dry despite aromatic intensity.",
    "Provence": "World-famous for pale, dry rosé. Also produces reds and whites, but rosé accounts for ~90% of production.",
    "Tuscany": "Home of Sangiovese — Chianti, Brunello di Montalcino, and Super Tuscans like Tignanello. Food-friendly wines with bright acidity.",
    "Piedmont": "Italy's Burgundy — Nebbiolo produces Barolo and Barbaresco. Elegant, powerful wines with high tannin and acidity that age beautifully.",
    "Veneto": "Diverse region producing Amarone (rich, dried-grape red), Prosecco (sparkling), Soave (white), and Pinot Grigio.",
    "Rioja": "Spain's most famous wine region. Tempranillo-based reds aged in American or French oak. Classified by aging: Crianza, Reserva, Gran Reserva.",
    "Priorat": "Small, intense Spanish region. Old-vine Grenache on slate soils produces concentrated, mineral reds. One of Spain's only DOCa regions.",
    "Ribera del Duero": "High-altitude Spanish region. Tempranillo (locally called Tinto Fino) produces powerful, age-worthy reds. Home of Vega Sicilia.",
    "Barossa Valley": "Australia's most famous wine region. Known for bold, full-bodied Shiraz with dark fruit, chocolate, and spice.",
    "McLaren Vale": "Warm Australian region south of Adelaide. Shiraz and Grenache dominate. Wines tend to be rich, concentrated, and generous.",
    "Napa Valley": "California's premier wine region. World-class Cabernet Sauvignon, opulent Chardonnay. Premium prices to match.",
    "Sonoma": "Napa's neighbor with more diverse climates. Cool-climate Pinot Noir and Chardonnay alongside warm-climate Zinfandel and Cabernet.",
    "Marlborough": "New Zealand's signature region. Explosive Sauvignon Blanc with tropical fruit and herbaceous notes. Also growing Pinot Noir reputation.",
    "Mendoza": "Argentina's wine heartland at the foot of the Andes. High-altitude vineyards produce outstanding Malbec at all price points.",
    "Douro": "Portugal's premier wine region, home to Port wine. Increasingly known for excellent dry reds from native grapes.",
    "Mosel": "Germany's most famous wine region. Steep slate vineyards produce ethereal Riesling — from bone-dry to lusciously sweet.",
    "Stellenbosch": "South Africa's Napa. Known for Cabernet Sauvignon, Bordeaux blends, and the uniquely South African Pinotage grape.",
    "Maipo Valley": "Chile's most prestigious red wine region. Bordeaux-style Cabernet Sauvignon benefits from warm days and cool Andean nights.",
    "Hawke's Bay": "New Zealand's Bordeaux — warm climate produces excellent Syrah, Merlot, and Cabernet Sauvignon.",
}

GRAPE_PROFILES: dict[str, dict] = {
    "Cabernet Sauvignon": {
        "body": "full",
        "taste": "Blackcurrant, cedar, tobacco, graphite",
        "pairs_with": ["beef", "lamb", "hard cheese"],
        "description": "The king of red grapes. Thick-skinned, tannic, age-worthy. Thrives in Bordeaux, Napa, and Chile.",
    },
    "Merlot": {
        "body": "medium-full",
        "taste": "Plum, chocolate, herbal notes",
        "pairs_with": ["roast chicken", "pork", "pasta"],
        "description": "Softer and rounder than Cabernet. Stars on Bordeaux's Right Bank (Pomerol, Saint-Emilion).",
    },
    "Pinot Noir": {
        "body": "light-medium",
        "taste": "Cherry, earth, mushroom, delicate spice",
        "pairs_with": ["duck", "salmon", "mushroom dishes"],
        "description": "The heartbreak grape — difficult to grow, magical when done right. Burgundy is its spiritual home.",
    },
    "Syrah": {
        "body": "full",
        "taste": "Blackberry, pepper, smoke, meaty",
        "pairs_with": ["grilled meat", "game", "BBQ"],
        "description": "Bold and spicy. Called Shiraz in Australia. Northern Rhone (Hermitage) vs New World (Barossa) = elegance vs power.",
    },
    "Sangiovese": {
        "body": "medium",
        "taste": "Cherry, tomato leaf, herbs, bright acidity",
        "pairs_with": ["pasta", "pizza", "grilled vegetables"],
        "description": "Italy's most planted grape. The backbone of Chianti, Brunello, and many Super Tuscans.",
    },
    "Tempranillo": {
        "body": "medium-full",
        "taste": "Cherry, leather, vanilla, tobacco",
        "pairs_with": ["lamb", "roast pork", "Manchego"],
        "description": "Spain's noble grape. Loves oak aging. Rioja's signature variety.",
    },
    "Nebbiolo": {
        "body": "full",
        "taste": "Rose petal, tar, truffle, cherry, high tannin",
        "pairs_with": ["truffle", "braised meat", "aged cheese"],
        "description": "Piedmont's treasure — produces Barolo and Barbaresco. Pale color belies immense structure.",
    },
    "Malbec": {
        "body": "full",
        "taste": "Plum, violet, dark chocolate, juicy",
        "pairs_with": ["steak", "empanadas", "BBQ"],
        "description": "Argentina made this grape famous. Inky, fruit-forward, crowd-pleasing. Great value at all levels.",
    },
    "Grenache": {
        "body": "medium-full",
        "taste": "Red berry, white pepper, herbs, warm",
        "pairs_with": ["Mediterranean food", "grilled meat", "stew"],
        "description": "Workhorse of Southern Rhone and Spain. Often blended. Priorat's old vines produce concentrated single-varietal wines.",
    },
    "Chardonnay": {
        "body": "medium-full",
        "taste": "Apple, butter, tropical fruit (depends on oak)",
        "pairs_with": ["lobster", "roast chicken", "creamy sauces"],
        "description": "The world's most popular white grape. Unoaked = crisp Chablis. Oaked = buttery California style.",
    },
    "Sauvignon Blanc": {
        "body": "light",
        "taste": "Grapefruit, grass, passionfruit, mineral",
        "pairs_with": ["seafood", "salad", "goat cheese"],
        "description": "Zingy and refreshing. Marlborough (NZ) = tropical. Loire = mineral. Always high acidity.",
    },
    "Riesling": {
        "body": "light",
        "taste": "Lime, green apple, petrol (aged), mineral",
        "pairs_with": ["spicy food", "Asian cuisine", "pork"],
        "description": "One of the world's greatest grapes. Ranges from bone-dry to dessert-sweet. Exceptional in Mosel and Alsace.",
    },
    "Chenin Blanc": {
        "body": "medium",
        "taste": "Honey, quince, apple, lanolin",
        "pairs_with": ["Thai food", "pork", "foie gras"],
        "description": "Loire Valley's chameleon — sparkling, dry, sweet. Also thrives in South Africa.",
    },
    "Pinot Grigio": {
        "body": "light",
        "taste": "Pear, citrus, almond, clean",
        "pairs_with": ["light pasta", "seafood", "salad"],
        "description": "Italy's easy-drinking white. Crisp and neutral — perfect aperitivo or light lunch wine.",
    },
    "Pinotage": {
        "body": "medium-full",
        "taste": "Dark berry, smoke, mocha, earthy",
        "pairs_with": ["BBQ", "game meat", "stew"],
        "description": "South Africa's unique grape — a cross of Pinot Noir and Cinsaut. Love-it-or-hate-it character.",
    },
}
