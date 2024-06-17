from datetime import datetime
import random

from redis import Redis

from pbot.middleware.base import Middleware
from pbot.utils import create_response


class TacoRecipes(Middleware):
    """
    """

    KEYWORDS = ["taco"]

    def __init__(self, redis: Redis) -> None:
        """
        """
        self.redis = redis

    def handle_messages(self, messages: list[dict]) -> list[dict]:
        messages.sort(key=lambda x: float(x["time"]), reverse=False) # Ascending.

        print(len(messages))

        for message in messages:

            # Ignore bot messages.
            if int(message["user"]["bot"]) == 1:
                continue

            # Ignore responded messages.
            if message["response"] == "" or message["response"] == None:
                for keyword in self.KEYWORDS:
                    if keyword.lower() in message["content"].lower():
                        # Create a GUID.
                        resp_id = f"taco{datetime.now().timestamp()}"

                        # Preach the gospel of tacos.
                        create_response(self.redis, resp_id, random.choice(TACO_RECIPES), message["id"])

                        # Move on to next message.
                        break

        return messages

BEEF_TACOS = """
***Alert! Beef tacos inbound!***

**Ingredients:**
- 1 lb ground beef
- 1 packet taco seasoning
- 1/2 cup water
- 8 small flour or corn tortillas
- 1 cup shredded lettuce
- 1 cup shredded cheddar cheese
- 1/2 cup diced tomatoes
- 1/4 cup diced onions
- Salsa and sour cream (optional)

**Instructions:**
1. In a skillet over medium heat, cook the ground beef until browned. Drain excess fat.
2. Add taco seasoning and water to the beef. Simmer for 5-7 minutes until thickened.
3. Warm the tortillas in a separate skillet or in the microwave.
4. Assemble tacos by adding beef, lettuce, cheese, tomatoes, and onions to each tortilla.
5. Top with salsa and sour cream if desired.
"""

CHICKEN_TACOS = """
***Get these chicken tacos in your tum tum!***

**Ingredients:**
- 1 lb boneless, skinless chicken breasts, cooked and shredded
- 1 packet taco seasoning
- 1/2 cup water
- 8 small flour or corn tortillas
- 1 cup shredded lettuce
- 1/2 cup diced avocado
- 1/2 cup shredded Monterey Jack cheese
- 1/4 cup chopped cilantro
- Lime wedges (optional)

**Instructions:**
1. In a skillet, combine shredded chicken, taco seasoning, and water. Cook over medium heat until heated through.
2. Warm the tortillas in a separate skillet or in the microwave.
3. Fill each tortilla with chicken, lettuce, avocado, cheese, and cilantro.
4. Serve with lime wedges on the side.
"""

FISH_TACOS = """
***It's time for fish tacos. Prepare yourselves.***

**Ingredients:**
- 1 lb white fish fillets (such as cod or tilapia)
- 2 tbsp olive oil
- 1 tsp chili powder
- 1/2 tsp garlic powder
- 1/2 tsp cumin
- 1/2 tsp paprika
- 8 small corn tortillas
- 1 cup shredded cabbage
- 1/2 cup diced mango
- 1/4 cup diced red onion
- Cilantro lime sauce (mix 1/2 cup sour cream with juice of 1 lime and 2 tbsp chopped cilantro)

**Instructions:**
1. Preheat oven to 375°F (190°C). Place fish on a baking sheet. Drizzle with olive oil and season with chili powder, garlic powder, cumin, and paprika.
2. Bake fish for 15-20 minutes, until it flakes easily with a fork.
3. Warm the tortillas in a separate skillet or in the microwave.
4. Flake the fish and divide it among the tortillas. Top with cabbage, mango, and red onion.
5. Drizzle with cilantro lime sauce before serving.
"""

VEGGIE_TACOS = """
***Veggie Taco Time!***

**Ingredients:**
- 1 tbsp olive oil
- 1 red bell pepper, sliced
- 1 yellow bell pepper, sliced
- 1 zucchini, sliced
- 1 red onion, sliced
- 1 tsp cumin
- 1 tsp chili powder
- 8 small corn tortillas
- 1/2 cup crumbled feta cheese
- 1/4 cup chopped cilantro
- Lime wedges (optional)

**Instructions:**
1. In a large skillet, heat olive oil over medium-high heat. Add bell peppers, zucchini, and red onion. Cook for 5-7 minutes until tender.
2. Season vegetables with cumin and chili powder.
3. Warm the tortillas in a separate skillet or in the microwave.
4. Fill each tortilla with sautéed vegetables. Top with feta cheese and cilantro.
5. Serve with lime wedges on the side.
"""

PORK_TACOS = """
***Cower in fear of these pork tacos...***

**Ingredients:**
- 2 lbs pork shoulder
- 1 onion, quartered
- 2 cloves garlic, minced
- 1 cup orange juice
- 1 tsp cumin
- 1 tsp oregano
- 1/2 tsp salt
- 8 small corn tortillas
- 1 cup chopped white onion
- 1 cup chopped cilantro
- Salsa verde (optional)

**Instructions:**
1. In a slow cooker, combine pork shoulder, onion, garlic, orange juice, cumin, oregano, and salt. Cook on low for 8 hours or until the pork is tender and can be shredded with a fork.
2. Shred the pork and return it to the slow cooker to absorb the juices.
3. Warm the tortillas in a separate skillet or in the microwave.
4. Fill each tortilla with carnitas. Top with chopped onion, cilantro, and salsa verde if desired.
"""

TACO_RECIPES = [BEEF_TACOS, CHICKEN_TACOS, FISH_TACOS, VEGGIE_TACOS, PORK_TACOS]
