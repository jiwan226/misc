import datetime
import gzip
import re
import os
import sys
import json
from ftplib import FTP


FTP_USER = "HerbalShisha.93203"
FTP_PW = "7eQnl44pFN+W#8"

advancements = []
ftp = FTP("147.135.97.128")
speedrun_name = None
world_name = None
start_time = None
output_file = None
output_filename = None

ID_MAP = {
    "3e12019a-951e-4488-83be-f089e542c616": "HerbalShisha",
    "00cefaab-ee76-49ca-91ed-3df21f8913f3": "junsus",
    "d34cc301-7ee5-4f4a-a262-2ecde5393c2c": "soonhokwon",
    "4c23bad0-4ded-4cd6-b870-58ccb674cbb8": "GChosen1",
}


def main():
    global speedrun_name, output_file, output_filename, start_time, world_name

    ftp.login(user=FTP_USER, passwd=FTP_PW)
    world_name = str(sys.argv[1])
    if len(sys.argv) <= 2:
        start_time = get_start_time()
    else:
        start_time = str(sys.argv[2])

    # Get starting timestamp
    start_timestamp = datetime.datetime.strptime(
        start_time, "%Y-%m-%d %H:%M:%S"
    ).timestamp()

    # Create directory for this speedrun
    try:
        ftp.cwd(world_name + "/advancements")
    except:
        print("Invalid World Name: %s\n" % sys.argv[1])
        raise

    speedrun_name = "speedrun_%s" % start_time[:10]
    if not os.path.exists(speedrun_name):
        os.makedirs(speedrun_name)

    output_filename = speedrun_name + "/" + speedrun_name + ".txt"
    output_file = open(output_filename, "w")
    output_file.write("Date: %s\n" % start_time[:10])
    output_file.write("World Name: %s\n" % world_name)
    output_file.close()

    print_divider()

    advancement_files = ftp.nlst()

    for i in range(len(advancement_files)):
        advancement_filename = advancement_files[i]
        # Ger player name based on UUID
        player_name = ID_MAP[advancement_filename[:-5]]
        # Transfer file to local directory
        localfile_name = "%s/%s.json" % (speedrun_name, player_name)
        localfile = open(localfile_name, "wb")
        ftp.retrbinary("RETR " + advancement_files[i], localfile.write)
        localfile.close()
        # Add player JSON to list
        adv_json = json.load(open(localfile_name))
        adv_json.update({"player": player_name})
        advancements.append(adv_json)

    time_dict = {}
    time_dict = {"Nether Entry": get_nether_entry()}
    print_min_time(convert_to_elapsed_time(time_dict, start_timestamp))

    time_dict = {"Nether Fortress Entry": get_fortress_entry()}
    print_min_time(convert_to_elapsed_time(time_dict, start_timestamp))

    time_dict = {"Ender Eye Creation": get_endereye_creation()}
    print_min_time(convert_to_elapsed_time(time_dict, start_timestamp))

    time_dict = {"Stronghold Entry": get_stronghold_entry()}
    print_min_time(convert_to_elapsed_time(time_dict, start_timestamp))

    time_dict = {"End Portal Entry": get_end_entry()}
    print_min_time(convert_to_elapsed_time(time_dict, start_timestamp))

    time_dict = {"Free the End": get_free_the_end()}
    print_min_time(convert_to_elapsed_time(time_dict, start_timestamp))

    print_divider()

    time_dict = {}
    time_dict.update({"Stone Tool Upgrade": get_stonetool_creation()})
    time_dict.update({"First Blood": get_first_blood()})
    display_rank(
        "Stone Tool Upgrade", convert_to_elapsed_time(time_dict, start_timestamp),
    )
    display_rank(
        "First Blood", convert_to_elapsed_time(time_dict, start_timestamp),
    )

    print_file()


def format_time(t):
    return "%dm %ds" % (t / 60, t % 60)


def print_file():
    output_file = open(output_filename, "r")
    print(output_file.read())
    output_file.close()


def print_divider():
    output_file = open(output_filename, "a")
    output_file.write("---------------------------------------\n")
    output_file.close()


def convert_to_elapsed_time(time_dict, start_timestamp):
    output_file = open(output_filename, "a")
    elapsed_time_dict = {}
    for adv, time_dict in time_dict.items():
        if len(time_dict.keys()) == 0:
            output_file.write("%s: Could Not Find \n" % adv)
        else:
            adv_time_dict = {}
            for player, t in time_dict.items():
                timestamp = int(
                    datetime.datetime.strptime(t, "%Y-%m-%d %H:%M:%S").timestamp()
                )
                elapsed_time = timestamp - start_timestamp
                adv_time_dict.update({player: elapsed_time})
            elapsed_time_dict.update({adv: adv_time_dict})
    output_file.close()
    return elapsed_time_dict


def print_min_time(elapsed_time_dict):
    output_file = open(output_filename, "a")
    min_time_dict = {}
    for adv, t_dict in elapsed_time_dict.items():
        min_time_dict.update({adv: min(t_dict.values())})

    for adv, min_time in min_time_dict.items():
        output_file.write("%s: %s\n" % (adv, format_time(min_time)))
    output_file.close()


def display_rank(advancement, time_dict):
    output_file = open(output_filename, "a")
    adv_dict = time_dict[advancement]
    output_file.write("%s Ranking\n" % advancement)
    times = list(adv_dict.values())
    times.sort()
    for i in range(len(times)):
        player = get_key(adv_dict, times[i])
        output_file.write("%d. %s: %s\n" % (i + 1, player, format_time(times[i])))
    output_file.write("\n")
    output_file.close()


def get_first_blood():
    first_blood = {}
    category = "minecraft:adventure/kill_a_mob"
    criteria = "killed_something"
    for adv_dict in advancements:
        try:
            times = list(adv_dict[category]["criteria"].values())
            entry = {adv_dict["player"]: times[0][:-6]}
            first_blood.update(entry)
        except:
            continue
    return first_blood


def get_stonetool_creation():
    stonetool_creation = {}
    category = "minecraft:story/upgrade_tools"
    criteria = "stone_pickaxe"
    for adv_dict in advancements:
        try:
            entry = {adv_dict["player"]: adv_dict[category]["criteria"][criteria][:-6]}
            stonetool_creation.update(entry)
        except:
            continue
    return stonetool_creation


def get_nether_entry():
    nether_entry = {}
    category = "minecraft:nether/root"
    criteria = "entered_nether"
    for adv_dict in advancements:
        try:
            entry = {adv_dict["player"]: adv_dict[category]["criteria"][criteria][:-6]}
            nether_entry.update(entry)
        except:
            continue
    return nether_entry


def get_fortress_entry():
    fortress_entry = {}
    category = "minecraft:nether/find_fortress"
    criteria = "fortress"
    for adv_dict in advancements:
        try:
            entry = {adv_dict["player"]: adv_dict[category]["criteria"][criteria][:-6]}
            fortress_entry.update(entry)
        except:
            continue
    return fortress_entry


def get_endereye_creation():
    endereye_creation = {}
    category = "minecraft:recipes/decorations/end_crystal"
    criteria = "has_ender_eye"
    for adv_dict in advancements:
        try:
            entry = {adv_dict["player"]: adv_dict[category]["criteria"][criteria][:-6]}
            endereye_creation.update(entry)
        except:
            continue
    return endereye_creation


def get_stronghold_entry():
    stronghold_entry = {}
    category = "minecraft:story/follow_ender_eye"
    criteria = "in_stronghold"
    for adv_dict in advancements:
        try:
            entry = {adv_dict["player"]: adv_dict[category]["criteria"][criteria][:-6]}
            stronghold_entry.update(entry)
        except:
            continue
    return stronghold_entry


def get_end_entry():
    end_entry = {}
    category = "minecraft:end/root"
    criteria = "entered_end"
    for adv_dict in advancements:
        try:
            entry = {adv_dict["player"]: adv_dict[category]["criteria"][criteria][:-6]}
            end_entry.update(entry)
        except:
            continue
    return end_entry


def get_free_the_end():
    free_end = {}
    category = "minecraft:end/kill_dragon"
    criteria = "killed_dragon"
    for adv_dict in advancements:
        try:
            entry = {adv_dict["player"]: adv_dict[category]["criteria"][criteria][:-6]}
            free_end.update(entry)
        except:
            continue
    return free_end


def get_key(d, val):
    for key, value in d.items():
        if val == value:
            return key


def get_start_time():
    global world_name, start_time

    if not os.path.exists("logs"):
        os.makedirs("logs")

    ftp.cwd("logs")
    log_filenames = ftp.nlst()

    log_string_list = []
    world_start_date = None
    for log_filename in log_filenames:
        localfile = open("logs/%s" % log_filename, "wb")
        ftp.retrbinary("RETR " + log_filename, localfile.write)
        localfile.close()

        if log_filename == "latest.log":
            localfile = open("logs/%s" % log_filename, "rb")
            log_string = str(localfile.read())
            log_string_list = log_string.split("\\n")
        else:
            localfile = gzip.open("logs/%s" % log_filename, "rb")
            log_string = str(localfile.read())
            log_string_list = log_string.split("\\n")

        world_start_message = [
            message
            for message in log_string_list
            if re.match('.*Preparing.*%s"' % world_name, message)
        ]
        if len(world_start_message) > 0:
            if log_filename == "latest.log":
                world_start_date = datetime.date.today()
            else:
                world_start_date = re.findall("\d\d\d\d-\d\d-\d\d", log_filename)[0]
            break

    time_set_message = [
        message
        for message in log_string_list
        if re.match(".*Set the time to 1000.*", message)
    ]
    time_set_message = time_set_message[0]
    start_time = re.findall("\d+:\d+:\d+", time_set_message)[0]
    start_date_time = "%s %s" % (world_start_date, start_time)
    ftp.cwd("../")
    return start_date_time


if __name__ == "__main__":
    main()
