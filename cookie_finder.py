#handles core logic 
from collections import defaultdict


def find_most_active_cookies(date, cookie_rows):
    #key = cookie, value = count for specific date 
    counts = defaultdict(int)
    for row in cookie_rows:
        cookie, timestamp = row.strip().split(",")
        row_date = timestamp.split("T")[0]
        if row_date == date:
            counts[cookie] += 1
    
    max_count = max(counts.values())
    return [cookie for cookie, count in counts.items() if count == max_count]

