import pickle
from multiprocessing import shared_memory

#this class handles writing pickle files into serialized memory
#it keeps track of the start and end of each pickle file so that I can point to them later
class SharedMemoryTableWriter:
    def __init__(self):
        self.offsets = {}  # filename → (start, end)
        self.current_offset = 0
        self.data_chunks = []

    def add(self, filename, obj):
        chunk = pickle.dumps(obj)
        start = self.current_offset
        end = start + len(chunk)
        self.offsets[filename] = (start, end)
        self.data_chunks.append(chunk)
        self.current_offset = end

    def finalize(self):
        #serialize full data block
        data_blob = b"".join(self.data_chunks)
        self.data_shm = shared_memory.SharedMemory(create=True, size=len(data_blob))
        self.data_shm.buf[:len(data_blob)] = data_blob

        #serialize offset table
        offset_blob = pickle.dumps(self.offsets)
        self.offset_shm = shared_memory.SharedMemory(create=True, size=len(offset_blob))
        self.offset_shm.buf[:len(offset_blob)] = offset_blob

        return {
            "data_name": self.data_shm.name,
            "data_size": len(data_blob),
            "offsets_name": self.offset_shm.name,
            "offsets_size": len(offset_blob)
        }

    def cleanup(self):
        self.data_shm.close()
        self.data_shm.unlink()
        self.offset_shm.close()
        self.offset_shm.unlink()

class SharedMemoryTableReader:
    def __init__(self, data_name, data_size, offsets_name, offsets_size):
        self.data_shm = shared_memory.SharedMemory(name=data_name)
        self.offsets_shm = shared_memory.SharedMemory(name=offsets_name)
        #create a memoryview of the data buffer once
        self.data_view = memoryview(self.data_shm.buf)
        self.offsets = pickle.loads(bytes(self.offsets_shm.buf[:offsets_size]))

    def get(self, filename):
        start, end = self.offsets[filename]
        return pickle.loads(bytes(self.data_view[start:end]))

    def cleanup(self):
        self.data_view.release()
        self.data_shm.close()
        self.offsets_shm.close()

def generate_list():
    with open("wordle_words", "r") as file:
        return [line.strip() for line in file]

def generate_guess_list():
    with open("dict", "r") as file:
        return [line.strip() for line in file]

#filters the word list for words that include the letter
def includes(word_list, letter):
    return [item for item in word_list if letter in item[0]]

#filters the word list for words that do not include the letter
def not_includes(word_list, letter):
    return [item for item in word_list if letter not in item[0]]

#filters the word list for words that have the letter in the position
def letter_in_place(word_list, letter, position):
    return [item for item in word_list if letter in item[0][position]]

#filters the word list for words that do not have the common letter in the right position
def includes_wrong_place(remaining_words, guess, word):
    for i in range(len(guess)):
        if guess[i] in word:
            if guess[i] != word[i]:
                remaining_words = [word for word in remaining_words if word[0][i] != guess[i]]
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
    with open(filename+ ".csv", mode="w", newline="") as file:
        for row in data:
            for row2 in row:
                file.write(str(row2) + "\n")


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

def add_row_numbers(data):
    return [[row, i] for i, row in enumerate(data, start=1)]

def conflate_guesses(list1, list2):
    return [a & b for a, b in zip(list1, list2)]

def sum_bits(n):
    return sum(int(bit) for bit in bin(n)[2:])