import game_class
import multiprocessing

def check_guess(guess):

    word_list = game_class.generate_list()
    max_remaining_words = 0
    remaining_words_len = [guess]

    for word in word_list:
        remaining_words = word_list

        #check if any letters are correct and in the right position
        letters_in_same_positon = game_class.compare_common_letters_position(word, guess)
        for position in letters_in_same_positon:
            #remove words without letter in the correct position
            remaining_words = game_class.letter_in_place(remaining_words, guess[position], position)

        #check if any letters are correct
        common_letters = game_class.compare_common_letters(guess, word)
        for letter in common_letters:
            #remove words without common letters
            remaining_words = game_class.includes(remaining_words, letter)

        #remove words with common letters in the wrong position
        remaining_words = game_class.includes_wrong_place(remaining_words, guess, word)

        #check if any letters are incorrect
        diff_letters = game_class.compare_diff_letters(guess, word)
        for letter in diff_letters:
            #remove words that contain the incorrect letters
            remaining_words = game_class.not_includes(remaining_words, letter)

        remaining_words_len.append(len(remaining_words))
        max_remaining_words = max(max_remaining_words, len(remaining_words))

    print(str(max_remaining_words) + " " + guess)
    return remaining_words_len


def main():
    """Main function to execute the program."""
    print("Program started")

    # init
    word_list = game_class.generate_list()
    guess_list = game_class.generate_guess_list()
    first_guess_results = []

    with multiprocessing.Pool(processes=multiprocessing.cpu_count()) as pool:
        first_guess_results.append(pool.map(check_guess, guess_list))

    #space to allow csv header to align correctly
    word_list.insert(0, "~")
    first_guess_results[0].insert(0, word_list)
    game_class.write_to_csv(first_guess_results, "first_guess_results.csv")

    # Cleanup and exit
    print("Program finished")

if __name__ == "__main__":
    main()