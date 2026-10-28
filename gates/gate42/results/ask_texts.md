# The only difference between the teams: this paragraph of the builder prompt

H, C and R are not written here: gates/gate42/referee/code_sheet.py appends them to runs/g42/ask_texts.md, as "There is
no product owner to ask..." plus the rules in exactly the words Hive gives its builders (hive.interview.instructions).
H gets the rule sheet from one interview as shipped; C gets the rule sheet written from N0's built code and corrected by
the owner; R gets the owner's complete rule sheet.

## N0 (nothing extra)
There is no product owner to ask on this project: `tools/ask.py` will tell you so. Work from the spec and the examples.

## H
There is no product owner to ask on this project: `tools/ask.py` will tell you so.

### The owner's rules for this feature (from his interview)
The owner decided each of these himself. Encode every one that touches your area as a test before you land, follow it exactly, and do not stretch it beyond the situation it describes.

- Whenever a rule asks whether a person born on 29 February is a given age, then in years that have no 29 February the birthday counts as 28 February. For example, Meera, born 29 February 2008, is 18 on 28 February 2026, so a shop's 18+ rule says yes.
- Whenever an invoice's due date is worked out, it is the issue date plus the payment terms in days. If that day is a Saturday or Sunday, the due date moves to the following Monday (for example, 1 October 2026 with 30-day terms is Saturday 31 October, so it is due Monday 2 November). Whenever an invoice is issued with payment terms of 0 days or a negative number (such as -10), accept it as is, with no rejection and no substitution of default terms. Its due date is its issue date, and the same weekend rule applies.
- Whenever the system adds a check digit to a supplier's product code, ignore the letters and dash and work out the digit from the numbers only (for 'INV-2041', use 2041).
- Whenever a late fee is worked out, no fee is charged unless the invoice is more than 5 days overdue. Once it is, the fee is 2% of the balance for every 30 days (or part of 30 days) the invoice is late, never less than 5.00 and never more than 50.00 (for example, Rohan's ₹10,000 invoice at 45 days would be 4%, capped at 50.00). Whenever a late fee is calculated, round it up to the next whole cent, never down or to the nearest, so any fraction of a cent above a cent boundary goes up to the next cent. A fee that is already exactly a whole cent stays as it is.
- Whenever a name is turned into a badge, split it into words and skip name particles such as 'van' and 'der'. Count titles (such as 'Dr.') and suffixes (such as 'Jr.') as ordinary words, and treat a hyphenated surname as a single word that gives one initial. The badge is the first letter of each remaining word, in order. For example, 'Dr. Anna van der Berg-Smith Jr.' gives 'DABJ'.
- Whenever a card number is entered for a receipt, always accept it, never refuse it and never raise an error. First remove every character that is not a digit (spaces, dashes, letters, anything else). If fewer than 12 digits remain, print one asterisk for every remaining digit (9 digits print as 9 asterisks, not a blank). If 12 or more digits remain, print every digit except the last 4 as an asterisk, followed by the last 4 digits. The result is one unbroken run with no spaces or grouping (4111 1111 1111 1234 prints ************1234).
- Apply these steps in order. (1) If the average score or the review count is missing, the label is blank. (2) Otherwise, if the average is below 0 or above 5, the label is "Invalid", whatever the review count. (3) Otherwise, if there are fewer than 5 reviews, the label is "Unrated". (4) Otherwise, round the average to one decimal place with halves rounded up (4.45 counts as 4.5), then label it "Excellent" if that rounded value is 4.5 or higher, "Good" if 3.5 or higher but below 4.5, "Fair" if 2.5 or higher but below 3.5, and "Poor" if below 2.5. There is no "Very Good" label (a 4.4 average from 200 reviews is "Good").
- Whenever a parcel's shipping charge is worked out, it depends only on the parcel's weight and zone, never on order value. There is no free-shipping threshold, so a 2 kg parcel costs the standard rate for 2 kg in its zone even when the basket is worth ₹2,500. Accept every weight, with no refusal and no weight limit. A parcel of 0 g or less is charged ₹0.00. For any heavier parcel, the number of blocks is the weight in grams divided by 500, rounded up. The charge is the zone's starting charge (₹9 for zone 2) + (blocks − 1) × ₹1 (2.5 kg is 5 blocks, so ₹9 + 4 × ₹1 = ₹13; 2.501 kg is 6 blocks, so ₹14). A parcel over 20 kg also gets a flat ₹25 added on top of that charge. In every zone, the total never goes above ₹99.00 (a 120 kg pallet is charged by weight as usual, then capped at ₹99.00).
- Whenever the survey score is computed, count only valid answers. A valid answer is a number from 0 to 10, and this includes a 7.5, which is neither a promoter nor a detractor and is counted in the total without capping or rounding. Skip blank answers, non-numeric answers and answers outside 0 to 10 (such as 11), excluding them from the total, and never reject the survey. If there are fewer than 5 valid answers, show no score. Otherwise the score is (promoters − detractors) ÷ total valid answers × 100, rounded to a whole number. Promoters are answers of 9 or 10, detractors are answers of 0 to 6, and the total includes the 7s and 8s.
- When an invoice is more than 5 days overdue but the customer's balance is ₹0 or a credit (for example ₹500 credit, 10 days past due), is a late fee charged? -> A. No late fee is charged when the balance is ₹0 or a credit, so the 5.00 minimum does not apply.

## R
There is no product owner to ask on this project: `tools/ask.py` will tell you so.

### The owner's rules for this feature (from his interview)
The owner decided each of these himself. Encode every one that touches your area as a test before you land, follow it exactly, and do not stretch it beyond the situation it describes.

- Whenever any argument of a scalar function (all functions except nps_score) is NULL, the function returns NULL.
- Whenever a numeric argument (balance_cents, days_late, terms_days, avg_score, review_count, weight_grams, zone) is not a number (for example text, even digit-only text), or is NaN or infinite, the function returns NULL; fractional numbers are accepted.
- Whenever a text argument of mask_card, normalize_sku, initials or invoice_check_digit is a whole integer, treat it as its decimal text; a non-integer number is NULL.
- Whenever a date argument of age_years or due_date is not exactly YYYY-MM-DD (surrounding whitespace is tolerated, nothing else is) or is not a real calendar date, the function returns NULL.
- Whenever late_fee gets balance_cents of zero or less, it returns 0.
- Whenever late_fee gets days_late of 5 or fewer (including zero and negatives), it returns 0; there is a 5-day grace period, and 5 days late is still free.
- Whenever late_fee charges a fee, it charges 2% of the balance for each started 30-day period late (days_late divided by 30, rounded up).
- Whenever the late_fee percentage amount is not a whole number of cents, round it up to the next cent.
- Whenever a late_fee would be below 500 cents, charge 500 cents (minimum fee), applied only when a fee is due at all.
- Whenever a late_fee would be above 5000 cents, charge 5000 cents (cap).
- Whenever due_date adds terms, it adds terms_days calendar days to invoice_date and returns the result as YYYY-MM-DD.
- Whenever terms_days given to due_date has a fractional part, round it down to a whole number of days before applying the other term rules.
- Whenever terms_days given to due_date is negative, treat it as 0.
- Whenever terms_days given to due_date is above 365, treat it as 365.
- Whenever the computed due date falls on a Saturday, due_date moves it forward 2 days to Monday.
- Whenever the computed due date falls on a Sunday, due_date moves it forward 1 day to Monday; weekdays are never moved.
- Whenever mask_card gets text, ignore every character that is not a digit (spaces, dashes, dots, letters) before masking.
- Whenever mask_card finds 12 or more digits, it returns one '*' for each digit except the last four, followed by those last four digits, with no separators.
- Whenever mask_card finds fewer than 12 digits, it masks every digit with '*' and shows none, returning one '*' per digit.
- Whenever mask_card finds no digits (empty text or letters only), it returns an empty string, not NULL.
- Whenever rating_label gets avg_score below 0 or above 5, it returns 'Invalid'; this check comes before the review-count check, so it applies even with few reviews.
- Whenever rating_label gets a valid avg_score and review_count below 5 (including zero and negatives), it returns 'Unrated'; exactly 5 reviews is enough to be rated.
- Whenever rating_label classifies a score, it first rounds the score to one decimal place, rounding halves up, and then applies the thresholds to the rounded value.
- Whenever the rounded rating_label score is 4.5 or more, return 'Excellent'.
- Whenever the rounded rating_label score is at least 3.5 and below 4.5, return 'Good'.
- Whenever the rounded rating_label score is at least 2.5 and below 3.5, return 'Fair'.
- Whenever the rounded rating_label score is below 2.5 (down to 0), return 'Poor'.
- Whenever normalize_sku gets text, remove leading and trailing whitespace and convert letters to uppercase.
- Whenever normalize_sku finds whitespace inside the text, replace each run of whitespace (any length) with a single hyphen.
- Whenever normalize_sku finds a character other than A-Z, 0-9 or hyphen (punctuation, underscores, accented or other non-ASCII letters), it deletes that character, after the whitespace-to-hyphen step.
- Whenever normalize_sku finds existing hyphens, keep them as they are: it never collapses repeated hyphens and never trims hyphens at the ends.
- Whenever normalize_sku ends up with an empty result (empty input, or nothing but removed characters), it returns NULL.
- Whenever shipping_cost gets weight_grams of zero or less, it returns 0, whatever the zone.
- Whenever shipping_cost prices a positive weight, the base charge is 500 cents for zone 1, 800 for zone 2 and 1200 for zone 3.
- Whenever shipping_cost gets a zone other than 1, 2 or 3 (zero, negative, above 3, or non-whole), it prices it as zone 3 and does not return NULL.
- Whenever shipping_cost prices a positive weight, it adds 100 cents for each started 500 grams of weight (weight divided by 500, rounded up).
- Whenever weight_grams is above 20000 (strictly), shipping_cost adds a 2500-cent oversize surcharge; exactly 20000 grams has no surcharge.
- Whenever the shipping_cost total would exceed 9900 cents, it returns 9900 (cap).
- Whenever initials gets a name, split it on whitespace (runs of whitespace and leading or trailing whitespace are ignored) and take the first character of each word, uppercased, in order.
- Whenever a word in initials is exactly one of the all-lowercase particles van, von, de, da, di, la, del, der, den, du, le, skip it; the same word with any capital letter (for example 'Van' or 'De') counts as a normal name word.
- Whenever initials meets a hyphenated or otherwise joined word, treat it as one word and use only its first character.
- Whenever initials produces no letters (empty text, only whitespace, or only particles), it returns NULL.
- Whenever invoice_check_digit gets text, ignore every non-digit character and work only with the digits.
- Whenever invoice_check_digit finds more than 12 digits, it uses only the last 12 digits and ignores the earlier ones.
- Whenever invoice_check_digit finds no digits (empty text or letters only), it returns NULL.
- Whenever invoice_check_digit computes the digit, it multiplies the digits by alternating weights 3 and 1 starting with weight 3 on the rightmost digit, sums them, and returns (10 minus the sum mod 10) mod 10, so the result is 0-9.
- Whenever age_years gets an as_of_date earlier than birth_date, it returns NULL; the same date gives 0.
- Whenever age_years computes age, it counts completed years: the year difference, minus one if the birthday (month and day) has not yet been reached on as_of_date.
- Whenever age_years gets a 29 February birth date and the as_of_date's year is not a leap year, it treats the birthday as 28 February, so the person ages on 28 February.
- Whenever nps_score receives a value that is NULL, not a number, below 0 or above 10, it ignores that row entirely (it counts neither in the total nor as promoter or detractor).
- Whenever nps_score classifies a valid value, 9 or more is a promoter, 6 or less is a detractor, and anything in between (including fractions such as 6.5 or 8.5) is passive.
- Whenever fewer than 5 valid values reach nps_score (including an empty column), it returns NULL.
- Whenever nps_score has 5 or more valid values, it returns (promoters minus detractors) divided by valid values times 100, rounded to a whole number with halves rounded away from zero (in both directions).

## C
There is no product owner to ask on this project: `tools/ask.py` will tell you so.

### The owner's rules for this feature (from his interview)
The owner decided each of these himself. Encode every one that touches your area as a test before you land, follow it exactly, and do not stretch it beyond the situation it describes.

- Whenever age_years is given a birth date and an as-of date, it returns the number of whole years between them, counting a birthday as reached on the as-of date itself.
- Whenever age_years is asked for a date before the person's birthday in that year, it returns one year less than the difference in calendar years.
- Whenever age_years is given a birth date of 29 February, the birthday counts as reached on 28 February in a year without a 29 February, so on 28 February of such a year the person has already turned a year older.
- Whenever age_years is given a birth date later than the as-of date, it returns NULL; if both dates are the same day it returns 0.
- Whenever age_years is given a NULL birth date or a NULL as-of date, it returns NULL.
- Whenever age_years is given a date that is not written as four-digit year, two-digit month and two-digit day separated by hyphens (for example 20000101 or 2000-1-1, or an empty text), or that does not exist on the calendar (for example month 13 or 30 February), it returns NULL.
- Whenever age_years is given a date followed by anything other than spaces or line breaks (including a time after a space or a 'T', for example 2000-01-01 10:00:00), it returns NULL. Spaces or line breaks before or after the date alone are ignored.
- Whenever age_years is given a date as a plain number instead of text (for example 20000101), it returns NULL.
- Whenever due_date is given an invoice date and a number of days, it first caps the number of days between 0 and 365: a negative number of days counts as 0, and a number of days over 365 counts as 365. It then returns the invoice date plus that many calendar days as YYYY-MM-DD, carrying over month ends and leap days (31 Jan 2024 + 30 days gives 2024-03-01; 28 Feb 2023 + 1 day gives 2023-03-01). If the resulting due date lands on a Saturday or Sunday, it moves forward to the next Monday.
- Whenever due_date is given 0 days or a negative number of days, it returns the invoice date itself, because negative terms count as 0 and never move the date earlier. If that date is a Saturday or Sunday, it still moves forward to the next Monday.
- Whenever due_date is given days with a fractional part, the fraction is rounded down to the whole day before the 0–365 cap applies, so 2.9 days counts as 2. Negative fractions also round down, but they then count as 0 because negative terms never move the date earlier.
- Whenever due_date is given the days as a real number, it uses that number. Days given as text, even numeric text like '30', ' 10 ', '2.9', '1e2' or '1_0', make it return NULL, and so does an empty text or any other non-number text ('abc', '', '12days'). A true/false value or binary data for the days also returns NULL, not 1 day.
- Whenever due_date is given a true/false value for the days it returns NULL, and whenever it is given binary data for the days it returns NULL.
- Whenever due_date is given a NULL invoice date or NULL days, it returns NULL.
- Whenever due_date is given an invoice date that is not a valid date written as YYYY-MM-DD (for example 'bad', a plain number such as 20240131, or a non-existent day), it returns NULL.
- Whenever due_date is given an invoice date followed by a time, whether after a space or a 'T', it is not accepted and the due date is NULL. Only spaces or line breaks before or after the date are ignored.
- Days over 365 count as 365, so a huge number of days is not an error. If days is infinite or non-numeric, due_date returns NULL. Only an invoice date within the last year before 9999-12-31 can push the due date past 9999-12-31; the policy does not define a result for that case.
- Whenever initials is given a full name, it returns the first character of each word, in capitals, with words separated by any run of spaces, tabs or line breaks; leading, trailing and repeated spaces are ignored ('  john   ronald  tolkien ' gives 'JRT').
- Whenever initials is given a name containing a hyphen, apostrophe or other punctuation inside a word, it does not split the word there, so 'jean-luc picard' gives 'JP' and 'mary-jane o'neil' gives 'MO'.
- Whenever a word given to initials starts with a quotation mark or other non-letter character, that character is used as its initial as it is ('"john" smith' gives '"S').
- Whenever initials is given a first letter with an accent or from a non-English alphabet, it capitalises it too ('élodie durand' gives 'ÉD'), and a letter whose capital is two letters is expanded ('ßeta' gives 'SS').
- Whenever initials is given an empty text, a text made only of spaces, or NULL, it returns NULL.
- Whenever initials is given a number instead of text, it treats the number as its text, so 12345 gives '1'.
- Whenever invoice_check_digit is given a code made only of the digits 0-9, it returns a single digit from 0 to 9. Only the last 12 digits of the code count, and any digits before them are ignored. Those 12 digits are weighted 3, 1, 3, 1 and so on, starting from the rightmost one, and summed. The result is whatever brings the sum up to the next multiple of 10 (4006381333931 gives 6 and 400638133393 gives 1).
- Whenever invoice_check_digit is given a code whose weighted sum is already a multiple of 10, it returns 0 (the code '0' gives 0).
- Whenever invoice_check_digit is given a code with leading zeros, the zeros are kept and count as digits (they add nothing to the sum, so '00012' gives the same digit as '12').
- Whenever invoice_check_digit is given a code, it throws away every character that is not a digit 0-9 (spaces, line breaks, hyphens, letters, minus signs, decimal points and non-Western digits, wherever they appear in the code) before the check digit is worked out, so '123-45', '12a' and '1.5' still give a digit. It returns NULL only when no digits are left at all (the code is empty, only spaces or only letters).
- Whenever invoice_check_digit is given an empty text, text of only spaces, or NULL, it returns NULL.
- Whenever invoice_check_digit is given a whole number rather than text, it treats it as the same digits (12345 gives 7), but a number with a decimal part such as 12.0 returns NULL.
- Whenever late_fee is given a positive balance in cents and a number of days late, it works as follows. For 1 to 5 days late, nothing is charged (the fee is 0). For 6 or more days late, the fee is 2% of the balance for each 30-day period late, with a part period counted as a full one: 6 to 30 days late is 2% of the balance, 31 to 60 days is 4%, 61 to 90 days is 6%, 91 to 120 days is 8%, and so on. The percentage keeps growing with no stop at 6%. Any fraction of a cent is rounded up to the next whole cent. When a fee is charged (6 or more days late), it is never below 500 cents and never above 5000 cents.
- Whenever late_fee is given a number of days late, fractions of a day are compared exactly with the limits. Anything up to and including 5 days late is not charged, so 0.5 days late is 0. Anything over 5 days, such as 5.5, is charged 2% (a part period counts as a full one). Anything over 30 days, such as 30.5, is charged 4%, and anything over 60 days, such as 60.5, is charged 6%, and so on for each further 30 days.
- Whenever late_fee calculates a fee that is not a whole number of cents, any fraction of a cent is rounded up to the next whole cent, not to the nearest (for example, 25,001 cents at 2% is 500.02 cents, and that is charged as 501). After that rounding, the fee is raised to 500 cents if it is below 500, and capped at 5000 cents if it is above 5000.
- Whenever late_fee is given zero or negative days late (not yet overdue), or a zero or negative balance, it returns 0 and charges nothing. The 500-cent minimum fee does not apply in that case, and neither does the 5-day grace rule.
- Whenever late_fee is given NULL for either the balance or the days late, it returns NULL, even if the other value is zero or negative, so NULL takes priority over the 'nothing to charge' rule.
- Whenever late_fee is given a balance or days late as text, including numeric text such as '500' or '10', late_fee returns NULL. late_fee also returns NULL when the balance or days late is an empty text or any text that is not a number, such as 'abc'. Only real numbers are accepted for the balance and the days late.
- Whenever late_fee is given a balance with a fractional cent (such as 10000.5), the balance is accepted as a real number. The percentage is applied to the exact value, any fraction of a cent in the fee is rounded up, and then the 500-cent minimum and 5000-cent maximum apply. For example, 100000.5 cents at 10 days late gives 2001 rather than 2000.
- Whenever mask_card is given a card number, it first removes all spaces and hyphens, then replaces every character except the last four with an asterisk, so '4111 1111 1111 1111' and '4111-1111-1111-1111' both give '************1111'.
- Whenever mask_card is given a number with four or fewer characters left after removing spaces and hyphens, it returns only asterisks, one per remaining character ('1234' gives '****', '123' gives '***'), so no digit is shown.
- Whenever mask_card is given an empty text or text of only spaces and hyphens, it returns an empty text, and whenever it is given NULL it returns NULL.
- Whenever mask_card is given characters other than digits 0-9, such as letters, dots, tabs, spaces or hyphens, every character that is not a digit 0-9 is thrown away before masking, so it is not counted, masked or shown. When fewer than 12 digits are left, the result is one asterisk per remaining digit, and no digit is shown. So '4111.1111' gives '********', and 'ab12' gives '**'. With 12 or more digits, every digit except the last four becomes an asterisk.
- Whenever mask_card is given spaces around the number, they are removed before masking; whenever it is given a number instead of text, it masks it the same way as its text.
- Whenever mask_card is given a number longer than 16 characters, it masks all but the last four in the same way, with no limit on length.
- Whenever normalize_sku is given a SKU, leading and trailing spaces are removed, and each run of spaces, tabs or line breaks becomes a single hyphen. Hyphens already in the SKU are kept as they are and are not merged, so '  abc   --  123  ' gives 'ABC----123'. All letters are made capital. Any character that is not a letter or digit (apart from hyphens) is thrown away, so 'a_b' gives 'AB'. If nothing is left, the result is NULL.
- Whenever normalize_sku is given a SKU that starts or ends with hyphens, the hyphens are kept, not removed ('-abc-' gives '-ABC-'), and a SKU made only of hyphens keeps them ('---' gives '---'). A SKU that is empty or only spaces gives NULL.
- Whenever normalize_sku is given letters with accents or from other alphabets, it throws them away, except ß, which becomes 'SS' and is kept; the plain English letters a-z become capitals ('élan-ß' gives 'LAN-SS').
- Whenever normalize_sku is given other separators such as underscores, slashes, dots or a longer dash (–), it throws them away, so 'a_b' gives 'AB' and 'a.b' gives 'AB'. Only letters, digits and hyphens survive, and spaces, tabs and line breaks turn into hyphens.
- Whenever normalize_sku is given a non-breaking space or other unusual space character, it treats it as a space and turns it into a hyphen.
- Whenever normalize_sku is given NULL it returns NULL, and whenever it is given a number it returns the number's text (12345 gives '12345').
- Whenever rating_label is given an average score and a review count: the score is first rounded to one decimal place, with halves rounded up. If there are fewer than 5 reviews, it returns 'Unrated', even with a perfect score. With at least 5 reviews, a rounded score of 4.5 or more returns 'Excellent' (so 4.45 counts as Excellent); a rounded score of 3.5 up to but not including 4.5 returns 'Good'; a rounded score of 2.5 up to but not including 3.5 returns 'Fair'; anything lower (down to 0) returns 'Poor'.
- Whenever rating_label is given a review count of zero or less and a valid average score, it returns 'Unrated' whatever the score is (a score of 0 with no reviews gives 'Unrated', not 'No reviews' or 'Poor'). It also returns 'Unrated' for any review count under 5, such as 0.5 reviews.
- Whenever rating_label is given a review count under 5 (including a count between 0 and 1, such as 0.5), it does not count as having reviews and returns "Unrated", whatever the score.
- Whenever rating_label is given an average score below 0 or above 5, it returns the label "Invalid", whatever the review count is, including zero reviews.
- Whenever rating_label is given a NULL score or a NULL review count, it returns NULL, even when the other value is zero.
- Whenever rating_label is given the score or the review count as text (even a numeric text such as '4.8') or an empty text, it returns NULL.
- Whenever shipping_cost is given a weight in grams and a delivery zone, it returns a base charge in cents of 500 for zone 1, 800 for zone 2 and 1200 for zone 3, plus 100 cents for each started 500 grams (1 to 500 grams is one step, 501 grams is two). A zone other than 1, 2 or 3 (such as 4, 0 or 1.5) is not rejected; it is charged like zone 3.
- Whenever shipping_cost is given a weight with a fraction of a gram (such as 0.5 or 500.5 or 1000.5), it still counts every started 500 grams as one step of 100 cents, so 0.5 grams is one step (100 cents), 500.5 grams is two steps, and 1000.5 grams is three steps.
- Whenever shipping_cost is given a weight of zero or less, it returns 0 (not NULL), and the base charge does not apply.
- Whenever shipping_cost is given a zone other than 1, 2 or 3 (such as 0, 4, a negative number or 1.5), it is not rejected: it is charged exactly like zone 3. A zone written as 2.0 is accepted as zone 2.
- Whenever shipping_cost is given a NULL weight or NULL zone, it returns NULL.
- Whenever shipping_cost is given the weight or the zone as text, even numeric text such as '500' or '2', or an empty text, it returns NULL.
- shipping_cost charges 200 cents per started kilogram of weight, in addition to the zone charge (for example, 100000 grams in zone 3 would be 20900 before the surcharge and cap below are applied). Any parcel over 20 kilograms (over 20,000 grams) gets a surcharge of 2,500 cents on top of the normal charge. The total shipping charge never goes above 9,900 cents, so 100,000 grams in zone 3 gives 9,900, not 20,900.
- Whenever nps_score is run over a column of survey scores, it returns the percentage of promoters (scores 9 and 10) minus the percentage of detractors (scores 0 to 6), where scores of 7 and 8 count as neutral but are included in the total.
- Whenever nps_score calculates a result that is not a whole number, it rounds to the nearest whole number with exactly one half rounded away from zero (66.67 gives 67, 12.5 gives 13, -12.5 gives -13).
- Whenever every valid response is a promoter nps_score returns 100, whenever every valid response is a detractor it returns -100, and whenever promoters and detractors are equal in number it returns 0.
- Whenever nps_score meets a NULL, a score below 0 or above 10, or a value stored as text, it ignores the row completely, so it does not count towards the total either.
- Whenever nps_score meets a score with a fraction, it uses its exact value: 9.5 and 9.0 count as promoters, 8.9 and 6.5 as neutral, 6.0 as a detractor.
- Whenever nps_score has fewer than 5 valid responses, it returns NULL. This includes the case where there are none at all (an empty column, only NULLs, only out-of-range values or only text). Responses that are NULL, below 0, above 10 or text are ignored and don't count as valid responses. So with 4 valid responses, or with 0, the result is NULL.
- Whenever nps_score is used with groups or a filter, it works out the score separately for the rows in each group or the rows that pass the filter. Asking for DISTINCT scores changes the result: only each different score is counted once, so duplicate responses are not counted. The 5-valid-response minimum applies to each group or filtered set on its own, and a group or filtered set with fewer than 5 valid responses gives NULL.
- Initials skip the lowercase name particles (van, von, de, da, di, la, del, der, den, du, le) but not capitalised ones, so "Vincent van Gogh" gives VG while "Jean Van Damme" gives JVD. Each space-separated word gives one initial, so "Mary-Jane Smith" gives MS, and a name with no initials left gives NULL. A person is NULL years old if the as-of date is before the birth date or if either date is not a valid YYYY-MM-DD date. A card number or code given as a whole number is accepted as if it were text, so 4111111111111111 is masked like the text version and 4006381333 gets a check digit.
