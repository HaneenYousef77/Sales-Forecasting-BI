import re

# Function to read file and sum numbers
def sum_numbers_in_file(filename):
    try:
        with open(filename, 'r') as file:
            content = file.read()
        
        # Extract numbers using regex
        numbers = re.findall('[0-9]+', content)
        
        # Convert numbers to integers
        numbers = [int(num) for num in numbers]
        
        # Calculate sum and count
        total_sum = sum(numbers)
        return total_sum

    except FileNotFoundError:
        return "Error: File not found."

# Example usage
total_sum = sum_numbers_in_file("data.txt")
print(total_sum)
