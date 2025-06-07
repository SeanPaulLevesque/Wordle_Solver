import game_class
import multiprocessing
import multiprocessing.shared_memory
import glob
import pickle

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
    first_guess_results = []


    with multiprocessing.Pool(processes=multiprocessing.cpu_count()) as pool:
        first_guess_results.append(pool.map(check_guess, guess_list))



def data_crunch():

    # init
    guess_list = game_class.generate_guess_list()

    # Get all pickle file paths
    pkl_files = glob.glob("guess_data/*.pkl")  # Adjust directory path

    # Use a generator to stream serialization without keeping all objects in memory
    serialized_data = b"".join(pickle.dumps(pickle.load(open(file, "rb"))) for file in pkl_files)

    #allocate shared memory
    shm = multiprocessing.shared_memory.SharedMemory(create=True, size=len(serialized_data))

    #write serialized data to shared memory
    shm.buf[: len(serialized_data)] = serialized_data

    #pack arguments as tuples (shared_memory_name, guess_list_item)
    args_list = [(shm.name, guess) for guess in guess_list[50:100]]

    #free up RAM
    #serialized_data = None

    with multiprocessing.Pool(processes=multiprocessing.cpu_count()) as pool:
        pool.map(process_combinations, args_list)


def process_combinations(args):

    #unpack arguments
    shm_name, guess = args

    print(guess)
    existing_shm = multiprocessing.shared_memory.SharedMemory(name=shm_name)

    #generate a list to acquire the index
    guess_dict = game_class.generate_guess_dict_sizes()
    #generate a dictionary to acquire the size of each data
    guess_list = game_class.generate_guess_list()

    guess_index = guess_list.index(guess)
    guess_start = guess_dict[guess_list[guess_index - 1]] if guess_index > 0 else 0
    guess_end = guess_dict[guess]
    guess1_data = pickle.loads(memoryview(existing_shm.buf[guess_start: guess_end]))

    for i, file in enumerate(guess_list):
        guess_start = guess_dict[guess_list[i - 1]] if i > 0 else 0
        guess_end = guess_dict[file]

        guess2_data = pickle.loads(memoryview(existing_shm.buf[guess_start: guess_end]))

        result = [a & b for a, b in zip(guess1_data, guess2_data)]

        #compute sum of binary digits for each number
        max_value = max(map(lambda num: bin(num).count("1"), result))

        if max_value <30:

            output_filename = f"second_guess_data/{guess} {file}.pkl"
            with open(output_filename, "wb") as f:
                pickle.dump(result, f)

    existing_shm.close()


if __name__ == "__main__":

    print("Program started")

    #data_collect()
    data_crunch()

    # Cleanup and exit
    print("Program finished")
