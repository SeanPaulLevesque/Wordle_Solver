import pandas as pd

def generate_df(filename):
    df = pd.read_csv(filename, names=["words"])
    return df

def generate_list(filename):
    with open(filename, "r") as file:
        return [line.strip() for line in file]


#filters the word list for words that include the letter
def includes(df, letter):
    return df[df["words"].str.contains(letter, case=False)]

def compare_common_letters_position(real_word, guess_word):
    #check which letters match in the same place and return position
    return [i for i, (c1, c2) in enumerate(zip(real_word, guess_word)) if c1 == c2]

#filters the word list for words that have the letter in the position
def letter_in_place(df, letter, position):
    return df[df["Word"].str[position] == letter]

def compare_common_letters(real_word, guess_word):
    #check which letters are common
    return "".join(sorted(set(real_word) & set(guess_word)))

#filters the word list for words that do not have the common letter in the right position
def includes_wrong_place(remaining_words, guess, word):
    for i in range(len(guess)):
        if guess[i] in word:
            if guess[i] != word[i]:
                remaining_words = remaining_words[remaining_words["Word"].str[i] != guess[i]]
    return remaining_words

#filters the word list for words that do not include the letter
def not_includes(word_list, letter):
    return word_list[~word_list["Word"].str.contains(letter, case=False, na=False)]

def compare_diff_letters(real_word, guess_word):
    #check which letters are in not in the word
    return "".join(sorted(set(real_word) - set(guess_word)))

def filter_list(remaining_words, guess, word):

    #check if any letters are correct and in the right position
    letters_in_same_positon = compare_common_letters_position(word, guess)
    for position in letters_in_same_positon:
        #remove words without letter in the correct position
        remaining_words = letter_in_place(remaining_words, guess[position], position)

    #check if any letters are correct
    common_letters = compare_common_letters(guess, word)
    for letter in common_letters:
        #remove words without common letters
        remaining_words = includes(remaining_words, letter)

    #remove words with common letters in the wrong position
    remaining_words = includes_wrong_place(remaining_words, guess, word)

    #check if any letters are incorrect
    diff_letters = compare_diff_letters(guess, word)
    for letter in diff_letters:
        #remove words that contain the incorrect letters
        remaining_words = not_includes(remaining_words, letter)

    return remaining_words