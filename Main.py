import game_class
import multiprocessing
import multiprocessing.shared_memory
import glob
import pickle
import time
import statistics
from collections import Counter
import os
import zipfile
import string
import csv

reader = None
files = [None]

def init_worker(meta):
    try:
        import psutil

        p = psutil.Process(os.getpid())

        # For Windows
        if hasattr(psutil, "BELOW_NORMAL_PRIORITY_CLASS"):
            p.nice(psutil.IDLE_PRIORITY_CLASS)  # Or BELOW_NORMAL_PRIORITY_CLASS for moderate throttling

    except Exception as e:
        print(f"[Init] Could not set low priority: {e}")

    global reader
    reader = game_class.SharedMemoryTableReader(**meta)
    global files
    files = glob.glob("C:/wordle/staging/second_guess_data/*.pkl")

def check_first_guess(guess):

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

def first_guess_data_collect():

    # init
    guess_list = game_class.generate_guess_list()

    with multiprocessing.Pool(processes=multiprocessing.cpu_count()) as pool:
        pool.map(check_first_guess, guess_list)


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
    for letter in string.ascii_lowercase[string.ascii_lowercase.index("a"):]:
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
        break

def third_guess_data_collect():

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
    for letter in string.ascii_lowercase[string.ascii_lowercase.index("a"):]:

        #unzip pickle files
        with zipfile.ZipFile("C:/wordle/second_guess_data/" + letter + ".zip", 'r') as zipf:
            for member in zipf.namelist():
                if not os.path.exists("C:/wordle/staging/second_guess_data/" + member):
                    zipf.extract(member, path="C:/wordle/staging/second_guess_data/")

        #pack arguments as tuples (metadata, guess_list_item)
        args_list = [(metadata, guess) for guess in guess_list]

        with multiprocessing.Pool(initializer=init_worker, initargs=(metadata,)) as pool:
            pool.map(process_third_guess, args_list)

        #file generation complete, put everything into a zip file
        source_folder = "C:/wordle/staging/third_guess_data/"
        output_folder = "C:/wordle/third_guess_data/"
        zip_filename = os.path.join(output_folder, f"{letter}.zip")

        files = glob.glob(os.path.join(source_folder, letter + "*"))

        with zipfile.ZipFile(zip_filename, 'w', compression=zipfile.ZIP_DEFLATED) as zipf:
            for filepath in files:
                arcname = os.path.relpath(filepath, start=source_folder)
                zipf.write(filepath, arcname=arcname)
                os.remove(filepath)
        break

def process_third_guess(args):

    #unpack arguments
    metadata, guess1 = args
    print(guess1)

    #point to shared memory
    guess1_data = reader.get(guess1)

    #load the guess2 list and filter down to remove common and double letters
    guess2_list = glob.glob("C:/wordle/staging/second_guess_data/*.pkl")
    guess2_list = [os.path.splitext(os.path.basename(word))[0]for word in guess2_list if not any(letter in os.path.splitext(os.path.basename(word))[0].lower() for letter in guess1.lower())
    ]
    if guess2_list:
        for guess2 in guess2_list:
            guess2_data = pickle.load(open("C:/wordle/staging/second_guess_data/" + guess2 + ".pkl", "rb"))

            result = [a & b for a, b in zip(guess1_data, guess2_data)]

            output_filename = os.path.join("C:/wordle/staging/third_guess_data", f"{guess2} {guess1}.pkl")
            with open(output_filename, "wb") as f:
                pickle.dump(result, f, protocol=pickle.HIGHEST_PROTOCOL)


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
        guess2_data = reader.get(guess2)

        result = [a & b for a, b in zip(guess1_data, guess2_data)]

        output_filename = os.path.join("C:/wordle/staging/second_guess_data", f"{guess1} {guess2}.pkl")
        with open(output_filename, "wb") as f:
            pickle.dump(result, f, protocol=pickle.HIGHEST_PROTOCOL)


def data_analyze(flag):

    #init shared memory writer
    writer = game_class.SharedMemoryTableWriter()

    #filter the guess list to remove words with double letters
    guess_list = game_class.generate_guess_list()
    guess_list = [word for word in guess_list if len(set(word)) == len(word)]

    #load all of the pickle files into memory serialized using the SharedMemoryTableWriter class
    for word in guess_list:
        writer.add(word, pickle.load(open("C:/wordle/first_guess_data/" + word + ".pkl", "rb")))

    metadata = writer.finalize()

    results = []

    for letter in string.ascii_lowercase[string.ascii_lowercase.index("f"):]:

        #unzip pickle files
        with zipfile.ZipFile("C:/wordle/second_guess_data/" + letter + ".zip", 'r') as zipf:
            for member in zipf.namelist():
                if not os.path.exists("C:/wordle/staging/second_guess_data/" + member):
                    zipf.extract(member, path="C:/wordle/staging/second_guess_data/")

        filtered_list = [item for item in guess_list if letter not in item]
        # pack arguments as tuples (metadata, guess_list_item)
        args_list = [(metadata, guess) for guess in filtered_list]

        with multiprocessing.Pool(initializer=init_worker, initargs=(metadata,)) as pool:
            pool.map(check_data_third_guess, args_list)


        files = glob.glob("C:/wordle/staging/second_guess_data/*.pkl")
        for file in files:
            os.remove(file)

        # files = glob.glob("C:/wordle/third_guess_data/*.csv")
        # os.mkdir("C:/wordle/staging/third_guess_data/+" + letter)
        # for file in files:
        #     os.

        break


#this opens a single pickle file and generates statistics and prints them to console
def check_data_first_guess(guess):

    combo_guess = pickle.load(open(guess, "rb"))
    print(guess)
    time.sleep(.04 )

    binary_numbers = [bin(n).count("1") for n in combo_guess]
    ones_count = list(map(lambda n: bin(n).count("1"), combo_guess))
    ones_count = Counter(ones_count)[1]
    min_count = min(binary_numbers)
    max_count = max(binary_numbers)
    quartiles = statistics.quantiles(binary_numbers, n=4)
    packing = [os.path.splitext(os.path.basename(guess))[0],min_count, quartiles[0], quartiles[1], quartiles[2], max_count, ones_count]
    return packing
    os.remove(guess)
    #print(f"{os.path.splitext(os.path.basename(guess))[0]} {min_count} {quartiles[0]} {quartiles[1]} {quartiles[2]} {max_count} {ones_count}\n")

#this takes a single pickle file and conflates it with every other pickle file and prints statistics to console
def check_data_third_guess(args):

    #unpack arguments
    metadata, guess1 = args
    print(guess1)

    time.sleep(.04)

    #point to shared memory
    guess1_data = reader.get(guess1)
    # Get all pickle file paths
    #combo2_list = glob.glob("C:/wordle/staging/second_guess_data/*.pkl")

    filtered_words = [
        os.path.splitext(os.path.basename(word))[0]
        for word in files
        if not set(guess1.lower()) & set(os.path.splitext(os.path.basename(word))[0].lower())
    ]
     results = []
    for combo2_guess in filtered_words:
        time.sleep(.01)
        combo2_data = pickle.load(open("C:/wordle/staging/second_guess_data/" + combo2_guess + ".pkl", "rb"))
        result = [a & b for a, b in zip(guess1_data, combo2_data)]

        binary_numbers = [bin(n).count("1") for n in result]
        ones_count = list(map(lambda n: bin(n).count("1"), result))
        ones_count = Counter(ones_count)[1]
        min_count = min(binary_numbers)
        max_count = max(binary_numbers)
        quartiles = statistics.quantiles(binary_numbers, n=4)
        #print(f"{combo2_guess} {guess1} {min_count} {quartiles[0]} {quartiles[1]} {quartiles[2]} {max_count} {ones_count}\n")

        results.append((guess1 + " " + combo2_guess, min_count, quartiles[0], quartiles[1], quartiles[2], max_count, ones_count))

    with open("C:/wordle/third_guess_data/" + guess1 + ".csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["word_combo", "min", "q1", "median", "q3", "max", "ones_count"])  # header row
        writer.writerows(results)  # write all rows at once



if __name__ == "__main__":

    print("Program started")

    combo2_list = glob.glob("C:/wordle/staging/second_guess_data/*.pkl")

    #first_guess_data_collect()
    #second_guess_data_collect()
    #third_guess_data_collect()
    #data_crunch()
    data_analyze("third_guess")

    # Cleanup and exit
    print("Program finished")
