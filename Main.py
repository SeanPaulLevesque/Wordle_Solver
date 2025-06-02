import game_class
import multiprocessing

def check_guess(guess):

    word_list = game_class.generate_list()
    word_list = game_class.add_row_numbers(word_list)
    remaining_words_bits = []
    print(guess)
    for word in word_list:
        remaining_words = word_list

        remaining_words = game_class.filter_list(remaining_words, guess, word[0])

        remaining_words_bits.append((sum([2 ** num[1] for num in remaining_words])))

    return remaining_words_bits

def main():
    """Main function to execute the program."""

    # init
    guess_list = game_class.generate_guess_list()
    first_guess_results = []

    with multiprocessing.Pool(processes=multiprocessing.cpu_count()) as pool:
        first_guess_results.append(pool.map(check_guess, guess_list))

    #game_class.write_to_csv(first_guess_results[0],"sixth_guess_results")


if __name__ == "__main__":

    print("Program started")

    main()

    # Cleanup and exit
    print("Program finished")