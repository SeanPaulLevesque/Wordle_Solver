import csv
from itertools import combinations


def generate_list():
    with open("wordle_words", "r") as file:
        return [line.strip() for line in file]

def generate_guess_list():
    with open("dict", "r") as file:
        return [line.strip() for line in file]

#filters the word list for words that include the letter
def includes(word_list, letter):
    return [item for item in word_list if letter in item]

#filters the word list for words that do not include the letter
def not_includes(word_list, letter):
    return [item for item in word_list if letter not in item]

#filters the word list for words that have the letter in the position
def letter_in_place(word_list, letter, position):
    return [item for item in word_list if letter in item[position]]

#filters the word list for words that do not have the common letter in the right position
def includes_wrong_place(remaining_words, guess, word):
    for i in range(len(guess)):
        if guess[i] in word:
            if guess[i] != word[i]:
                remaining_words = [word for word in remaining_words if word[i] != guess[i]]
    return remaining_words

def compare_common_letters_position(real_word, guess_word):
    #check which letters match in the same place and return position
    return [i for i, (c1, c2) in enumerate(zip(real_word, guess_word)) if c1 == c2]

def compare_common_letters(real_word, guess_word):
    #check which letters are common
    return "".join(sorted(set(real_word) & set(guess_word)))

def compare_diff_letters(real_word, guess_word):
    #check which letters are in not in the word
    return "".join(sorted(set(real_word) - set(guess_word)))

def write_to_csv(data, filename):
    with open(filename, mode="w", newline="") as file:
        for row in data:
            for row2 in row:
                file.write(str(row2) + "\n")