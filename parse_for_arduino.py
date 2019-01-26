# USAGE: 
# python3 parse_for_arduino.py > output_for_arduino.txt

import os
from os import listdir
from os.path import isfile
files = [f for f in os.listdir('./resources') if (os.path.isfile(f'./resources/{f}')) and ("properties" in f) and not f.startswith("keyboard")]

# Exclude Russian (it is a bit longer than others and for my project I need to keep encoding array lenght under 100 bytes) 
# With Russian - Array length = 3x 119
# Without Russian - Array length = 3x 78
del files[files.index("ru.properties")]

def get_keys():
    keys_dict = {}
    with open("resources/keyboard.properties", "rt") as f:
        for line in f.readlines():
            if line.startswith("MOD") or line.startswith("KEY"):
                key = line.split("=")[0].strip()
                value = line.split("=")[1].strip()
                base = 16 if "x" in value else 10
                keys_dict[key] = int(value, base)
    return keys_dict

def add_modifiers(modifiers):
    binary_sum = 0
    for m in modifiers:
        binary_sum |= m
    return binary_sum

languages = []

for f_name in files:
    keys_dict = get_keys()
    key_map = []
    ascii_values = []
    key_codes = []
    modifiers = []
    with open(f'./resources/{f_name}', "rt") as f:
        lines = f.readlines()
        for line in lines:
            if line.startswith("KEY"): 
                key = line.split("=")[0].strip()
                value = line.split("=")[1].strip()
                base = 16 if "x" in value else 10
                # if "BACKSLASH" in key:
                #     print("BACKSLASH")
                #     print("BASE =", base)
                #     print("value=", int(value,base))
                # if "HASH" in key:
                #     print("HASH")
                #     print("BASE =", base)
                #     print("value=", int(value,base))
                keys_dict[key] = int(value, base)

        for line in lines:
            if line.startswith("ASCII") or line.startswith("ISO") and "BITS" not in line and "KEY_11" not in line: # line.startswith("UNICODE") or 
                key = line.split("=")[0].strip()
                ASCII = int(key.split("_")[-1], 16)
                value = line.split("=")[1].strip()
                keys_to_press = [keys_dict[v.strip()] for v in value.split(",")]
                ascii_values.append(ASCII)
                key_codes.append(keys_to_press[0])
                modifiers.append(0 if len(keys_to_press) == 1 else add_modifiers(keys_to_press[1:]))

    # print(f_name)
    # print("byte encoding[{}] =".format(len(ascii_values)), "{")
    # print("    {", ",".join(str(a) for a in ascii_values), "},")
    # print("    {", ",".join(str(k) for k in key_codes), "},")
    # print("    {", ",".join(str(m) for m in modifiers), "},")
    # print("};")

    # print("Tranmission strings:")
    # print("ENC,D:{},end".format("".join(["{:X}".format(v) for v in ascii_values])))
    # print("ENC,U:{},end".format("".join(["{:X}".format(v) for v in key_codes])))
    # print("ENC,M:{},end".format("".join(["{:X}".format(v) for v in modifiers])))
    
    languages.append([ascii_values, key_codes, modifiers])

# check what characters are typed exactly the same way on every language (to save space in Arduino code - smaller array)
# That list can be saved to PROGMEM, it can also replace ascii_map from Keyboard library (Keyboard.cpp)
# Or just type these keys using the original Keyboard.press()
def get_ascii_that_is_always_typed_the_same_way():
    ascii_list = []
    base_lang = languages[9] # 9th had the most values (119)
    for ascii_val, key_code, modifier in zip(*base_lang):
        the_same = True
        for i, lang in enumerate(languages):
            if not (ascii_val in lang[0]):
                the_same = False
            else:
                ind = lang[0].index(ascii_val)
                if lang[1][ind] != key_code or lang[2][ind] != modifier:
                    the_same = False
        if the_same:
            ascii_list.append(ascii_val)
            # print(ascii_val, key_code, modifier)
    return ascii_list

ascii_that_does_not_need_encoding = get_ascii_that_is_always_typed_the_same_way()

def filter_encoding():
    for ascii_val in ascii_that_does_not_need_encoding:
        for lang in languages:
            if not ascii_val in lang[0]:
                continue
            else:
                ind = lang[0].index(ascii_val)
                del lang[0][ind]
                del lang[1][ind]
                del lang[2][ind]

filter_encoding()

max_length = 0
for lang in languages:
    if len(lang[0]) > max_length:
        max_length = len(lang[0])
                
print('''
Structure is:
byte encoding[3][max_length_of_any_lang_data] = {
    { ASCII characters that need to be typed },
    { USB HID scan codes },                 
    { USB HID scan codes - modifiers }, 
};
// USB HID scan codes reference: https://gist.github.com/MightyPork/6da26e382a7ad91b5496ee55fdc73db2


''')

for lang, f_name in zip(languages, files):
    ascii_values = lang[0]
    key_codes = lang[1]
    modifiers = lang[2]
            
    print(f_name)
    print("byte encoding[3][{}] =".format(max_length + 1), "{")
    print("    {", ",".join(str(a) for a in ascii_values), "},")
    print("    {", ",".join(str(k) for k in key_codes), "},")
    print("    {", ",".join(str(m) for m in modifiers), "},")
    print("};")

    print()
    print("Tranmission strings:")
    print("ENC,D:{},end".format("".join(["{:0{}X}".format(v,2) for v in ascii_values])))
    print("ENC,U:{},end".format("".join(["{:0{}X}".format(v,2) for v in key_codes])))
    print("ENC,M:{},end".format("".join(["{:0{}X}".format(v,2) for v in modifiers])))

    print()
    print("{},{},{},{}".format(
            f_name.split(".")[0], 
            "".join(["{:0{}X}".format(v,2) for v in ascii_values]),
            "".join(["{:0{}X}".format(v,2) for v in key_codes]),
            "".join(["{:0{}X}".format(v,2) for v in modifiers])
            )
        )

    print("\n\n") 

