import game_class
import multiprocessing
import multiprocessing.shared_memory
import glob
import pickle
import time
import statistics
from collections import Counter
import os
import pandas as pd
from pandasgui import show
import zipfile
import string

reader = None

def init_worker(meta):
    global reader
    reader = game_class.SharedMemoryTableReader(**meta)

def check_guess(guess):

    word_list = game_class.generate_list()
    word_list = game_class.add_row_numbers(word_list)
    remaining_words_bits = []
    print(guess)
    for word in word_list:
        remaining_words = word_list

        remaining_words = game_class.filter_list(remaining_words, guess, word[0])

        remaining_words_bits.append((sum([2 ** num[1] for num in remaining_words])))

    with open("guess_data/" + guess + ".pkl", "wb") as f:
        pickle.dump(remaining_words_bits, f)

    return

def data_collect():

    # init
    guess_list = game_class.generate_guess_list()

    check_guess(guess_list)

    with multiprocessing.Pool(processes=multiprocessing.cpu_count()) as pool:
        pool.map(check_guess, guess_list)


def data_crunch():

    #init shared memory writer
    writer = game_class.SharedMemoryTableWriter()

    #filter the guess list to remove words with double letters
    guess_list = game_class.generate_guess_list()
    guess_list = [word for word in guess_list if len(set(word)) == len(word)]

    #load all of the pickle files into memory serialized using the SharedMemoryTableWriter class
    for word in guess_list:
        writer.add(word, pickle.load(open("C:/wordle/first_guess_data/" + word + ".pkl", "rb")))

    metadata = writer.finalize()

    #chunk one letter at a time to save on disk space
    #using slices so that I can continue from where I last left off
    for letter in string.ascii_lowercase[string.ascii_lowercase.index("g"):]:
        #generate the list of words to check and then filter out words with double and common letters
        guess_list = game_class.generate_guess_list()
        guess_list = [word for word in guess_list if len(set(word)) == len(word)]
        guess_list = [word for word in guess_list if word.lower().startswith(letter)]

        #pack arguments as tuples (metadata, guess_list_item)
        args_list = [(metadata, guess) for guess in guess_list]

        with multiprocessing.Pool(initializer=init_worker, initargs=(metadata,)) as pool:
            pool.map(process_combinations, args_list)

        #file generation complete, put everything into a zip file
        source_folder = "C:/wordle/staging/second_guess_data/"
        output_folder = "C:/wordle/second_guess_data/"
        zip_filename = os.path.join(output_folder, f"{letter}.zip")

        files = glob.glob(os.path.join(source_folder, letter + "*"))

        with zipfile.ZipFile(zip_filename, 'w', compression=zipfile.ZIP_DEFLATED) as zipf:
            for filepath in files:
                arcname = os.path.relpath(filepath, start=source_folder)
                zipf.write(filepath, arcname=arcname)
                os.remove(filepath)

#this takes in a guess and then conflates it with every other guess
#it generates a pickle file into C:/wordle/staging
#then it pulls all of the pickle files together into a zip file to save disk space
def process_combinations(args):

    #unpack arguments
    metadata, guess1 = args
    print(guess1)

    #point to shared memory
    guess1_data = reader.get(guess1)

    #load the guess2 list and filter down to remove common and double letters
    guess2_list = game_class.generate_guess_list()
    guess2_list = [word for word in guess2_list if not any(letter in word for letter in guess1)]
    guess2_list = [word for word in guess2_list if len(set(word)) == len(word)]

    for guess2 in guess2_list:
        time.sleep(0.01)
        guess2_data = reader.get(guess2)

        result = [a & b for a, b in zip(guess1_data, guess2_data)]

        output_filename = os.path.join("C:/wordle/staging/second_guess_data", f"{guess1} {guess2}.pkl")
        with open(output_filename, "wb") as f:
            pickle.dump(result, f)


def data_analyze():

    # Get all pickle file paths
    args_list = glob.glob("C:/wordle/second_guess_data/*.pkl")
    print("guess 1st 2nd 3rd 4th 1count 2count 3count 4count")

    with multiprocessing.Pool(processes=multiprocessing.cpu_count()) as pool:
        pool.map(check_data_single, args_list)

#this opens a single pickle file and generates statistics and prints them to console
def check_data_single(guess):

    combo_guess = pickle.load(open(guess, "rb"))

    binary_numbers = [bin(n).count("1") for n in combo_guess]
    ones_count = list(map(lambda n: bin(n).count("1"), combo_guess))
    ones_count = Counter(ones_count)[1]
    min_count = min(binary_numbers)
    max_count = max(binary_numbers)
    quartiles = statistics.quantiles(binary_numbers, n=4)
    print(f"{os.path.splitext(os.path.basename(guess))[0]} {min_count} {quartiles[0]} {quartiles[1]} {quartiles[2]} {max_count} {ones_count}\n")

#this takes a single pickle file and conflates it with every other pickle file and prints statistics to console
def check_data_double(combo1_guess):

    combo1_data = pickle.load(open(combo1_guess, "rb"))
    # Get all pickle file paths
    combo2_list = glob.glob("second_guess_data/*.pkl")

    filtered_words = [os.path.splitext(os.path.basename(word))[0] for word in combo2_list if not any(letter in word for letter in combo1_guess)]

    for combo2_guess in filtered_words:
        combo2_data = pickle.load(open(combo2_guess, "rb"))
        result = [a & b for a, b in zip(combo1_data, combo2_data)]
        combo1_filename = os.path.splitext(os.path.basename(combo1_guess))[0]
        combo2_filename = os.path.splitext(os.path.basename(combo2_guess))[0]

        binary_numbers = [bin(n).count("1") for n in result]
        ones_count = list(map(lambda n: bin(n).count("1"), result))
        ones_count = Counter(ones_count)[1]
        min_count = min(binary_numbers)
        max_count = max(binary_numbers)
        quartiles = statistics.quantiles(binary_numbers, n=4)
        print(f"{combo1_filename} {combo2_filename} {min_count} {quartiles[0]} {quartiles[1]} {quartiles[2]} {max_count} {ones_count}\n")

        output_filename = f"fourth_guess_data/{combo1_filename} {combo2_filename}.pkl"
        with open(output_filename, "wb") as f:
            pickle.dump(result, f, protocol=pickle.HIGHEST_PROTOCOL)

def check_data2(args_list):

    guess1_data, guess2 = args_list
    print(guess2)
    third_guess = "dampy"
    guess3_data = pickle.load(open("guess_data/" + third_guess + ".pkl", "rb"))
    fourth_guess = glob.glob("guess_data/*.pkl")  # Adjust directory path
    for guess4 in fourth_guess:
        time.sleep(0.02)
        guess4_data = pickle.load(open(guess4, "rb"))

        guess2_data = pickle.load(open("guess_data/" + guess2 + ".pkl", "rb"))
        result = [a & b for a, b in zip(guess1_data, guess2_data)]
        result = [a & b for a, b in zip(result, guess3_data)]
        result = [a & b for a, b in zip(result, guess4_data)]
        # compute sum of binary digits for each number
        max_combo = max(map(lambda num: bin(num).count("1"), result))
        ones_count = list(map(lambda n: bin(n).count("1"), result))
        count = Counter(ones_count)[1]
        if count > 2200:
            print("count " + guess2 + " " + guess4 + " " + " " + str(count))
        # binary_numbers = [bin(n).count("1") for n in result]
        # quartiles = statistics.quantiles(binary_numbers, n=4)
        # third_quartile = quartiles[2]  # Q3 (75th percentile)
        #
        # if third_quartile < 2:
        #     print(f"Third quartile: {guess4} {third_quartile} ")

        if max_combo <3:
        #     print(file.split("\\")[-1] + " " + str(max_combo))
            print("Max " + guess2 + " " + guess4 + " " + " " + str(max_combo))

if __name__ == "__main__":

    print("Program started")
    # dtype_map = {0: str, 1: str, 2: int, 3: int, 4: int, 5: int, 6: int, 7: int}
    # df = pd.read_csv(r"C:\Users\Sean\Downloads\test - Copy.csv",
    #                  sep=r"\s+",  # Treat consecutive whitespace as delimiter
    #                  skip_blank_lines=True,
    #                  dtype={"guess1": str, "guess2": str, "min": int, "1stq": int, "median": int, "3rdq": int, "max": int, "count": int})  # Skip empty rows automatically
    #
    # gui = show(df)

    # letter = "c"
    # source_folder = "second_guess_data/"
    # zip_filename = letter + ".zip"
    #
    # files = glob.glob(os.path.join(source_folder, letter + "*"))  # Only top-level files starting with 'a'
    #
    # with zipfile.ZipFile(zip_filename, 'w', compression=zipfile.ZIP_DEFLATED) as zipf:
    #     for filepath in files:
    #         print(filepath)
    #         arcname = os.path.relpath(filepath, start=source_folder)
    #         zipf.write(filepath, arcname=arcname)
    #data_collect()
    data_crunch()
    #data_analyze()

    # Cleanup and exit
    print("Program finished")