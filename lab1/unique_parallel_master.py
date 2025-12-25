from Pyro4 import expose
import json
import re

class Solver:
    def __init__(self, workers=None, input_file_name=None, output_file_name=None):
        self.workers = workers
        self.input_file_name = input_file_name
        self.output_file_name = output_file_name

    def solve(self):
        print("Job Started")
        print("Workers %d" % len(self.workers))

        # read input
        text = self.read_input()
        
        # Split text into words
        words = text.strip().split()
        if not words:
            print("Input file is empty")
            self.write_output(json.dumps({}))
            return

        # Calculate words per worker
        words_per_worker = len(words) // len(self.workers)
        mapped = []

        # MAP phase - count word frequencies in each part
        for i in range(len(self.workers)):
            start = i * words_per_worker
            if i == len(self.workers) - 1:
                # Last worker gets all remaining words
                end = len(words)
            else:
                end = (i + 1) * words_per_worker
                
            # Get complete words for this worker
            worker_words = words[start:end]
            text_part = ' '.join(worker_words)
            mapped.append(self.workers[i].mymap(text_part))

        # REDUCE phase - combine all word counts
        result = self.myreduce(mapped)

        # write output
        self.write_output(json.dumps(result, indent=2))

    @staticmethod
    @expose
    def mymap(text_part):
        # Count word frequencies in this text part
        word_counts = {}
        words = text_part.lower().split()
        
        for word in words:
            # Clean the word: remove punctuation, keep alphanumeric characters
            clean_word = re.sub(r'[^\w\s]', '', word).strip()
            if clean_word:  # Only count non-empty strings
                word_counts[clean_word] = word_counts.get(clean_word, 0) + 1
        
        return word_counts

    @staticmethod
    @expose
    def myreduce(mapped):
        # Combine word counts from all workers
        total_counts = {}
        
        for worker_result in mapped:
            worker_counts = worker_result.value
            for word, count in worker_counts.items():
                total_counts[word] = total_counts.get(word, 0) + count
        
        # Sort by count (descending) and then alphabetically
        sorted_counts = dict(sorted(
            total_counts.items(),
            key=lambda x: (-x[1], x[0])  # Sort by count desc, then word asc
        ))
        
        return sorted_counts

    def read_input(self):
        with open(self.input_file_name, 'r') as f:
            return f.read()

    def write_output(self, output):
        with open(self.output_file_name, 'w') as f:
            f.write(output)
