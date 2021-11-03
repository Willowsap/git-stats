from random import *
from pprint import *
rounds = 10000
num_wins = 0
stats = {
    "normal": 0,
    "elite": 0,
    "boss": 0,
    "avg_time": 0.0
}
while num_wins < rounds:
    enemy = "normal"
    num_tries = 0
    had_drop = False
    while not had_drop:
        num_tries += 1
        if enemy == "normal":
            dropped = randint(1, 1500000)
        elif enemy == "elite":
            dropped = randint(1, 1500)
        else:
            dropped = 1
        if dropped == 1:
            num_wins += 1
            stats[enemy] = stats[enemy] + 1
            stats["avg_time"] += num_tries
            had_drop = True
        enemy = "normal"
        elite_spawn = randint(1, 50)
        if elite_spawn == 1:
            enemy = "elite"
            boss_spawn = randint(1, 1500)
            if boss_spawn == 1:
                enemy = "boss"
stats["avg_time"] = stats["avg_time"] / rounds
stats["normal"] = stats["normal"] / rounds * 100
stats["elite"] = stats["elite"] / rounds * 100
stats["boss"] = stats["boss"] / rounds * 100
pprint(stats)
