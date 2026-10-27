# Question plan for the 20 business functions

Budget: 30 questions to the product owner (one SELECT, one row, at most 3 values, one function per
question). Every answer becomes `tests/visible/<function>_qNN.json`.

What the examples already settle is listed first; the open input classes follow. Classes marked
(*) are the ones I think matter most and will ask about first.

## discount(price, tier)
Known: gold -20%, silver -10%, bronze -5%; result is REAL (190.0, 48.0, 72.0).
Open: (*) unknown tier ('platinum', '') -> price unchanged, NULL or error; (*) letter case / spaces
('GOLD', ' gold '); (*) NULL price / NULL tier; rounding of fractional prices (2 decimals?);
negative or zero price; very large price (cap on the discount?); integer vs real result for
unknown tier.

## shipping(weight_kg, zone)
Known (integers): local 1kg=5; national 1kg=10, 3kg=14; intl 2kg=27. National looks like 8+2/kg.
Open: (*) the per-kg formula for local and intl (local 2kg? intl 1kg, 5kg?); (*) fractional weight
(round up to whole kg? prorate?); (*) zero / negative weight; heavy-parcel threshold or surcharge;
unknown zone; case of zone; NULL arguments.

## abbrev(s, n)
Known: len(s) > n -> first n-1 chars + '~'; short strings unchanged.
Open: (*) len(s) == n; (*) n = 1, n = 0, negative n; empty s; NULL s / NULL n; trailing space
before the '~'.

## weekday(date)
Known: 'Mon'..'Fri' three-letter English names.
Open: (*) Sat/Sun names; (*) invalid date ('2024-02-30', 'hello', ''); NULL; datetime text with a
time part; non-leap Feb 29.

## age(birth, on)
Known: whole years, birthday counts on the day itself.
Open: (*) Feb 29 birthday on 28 Feb / 1 Mar of a non-leap year; (*) `on` before `birth` (negative,
0, NULL?); same day (0); NULL; invalid date.

## phone_fmt(s)
Known: 10 digits in any punctuation -> '(555) 123-4567'.
Open: (*) 11 digits with leading 1 / '+1'; (*) wrong digit count (7, 9, 12) -> unchanged, NULL?;
empty text; NULL; letters mixed in; surrounding spaces.

## band(x)
Known: 2, 5 -> 'low'; 30 -> 'mid'; 99 -> 'high'.
Open: (*) the two thresholds (somewhere in 6..29 and 31..98) and which side each boundary falls on;
(*) negative and zero; fractional values next to a boundary; NULL; very large values.

## roman(n)
Known: standard subtractive numerals (IV, MCMXCIV, MMXXIV).
Open: (*) 0 and negative; (*) > 3999; fractional n (truncate/round?); NULL; 3999 itself.

## ordinal(n)
Known: 21st, 22nd, 5th.
Open: (*) 11th/12th/13th teens and 111/112/113; (*) 0 and negative; NULL; fractional; 23rd.

## split_part(s, sep, idx)
Known: 1-based index, single-char separator.
Open: (*) idx beyond the field count ('' or NULL?); (*) idx 0 / negative (count from the end?);
separator absent; empty separator; multi-char separator; empty fields ('a,,b'); NULL args.

## median3(a, b, c)
Known: integer median of three integers.
Open: (*) NULL in one argument (median of the other two? NULL?); fractional values / mixed
int-real; ties; negative values; text arguments.

## stars(rating)
Known: n '*' characters, no padding to 5.
Open: (*) fractional rating (3.5 -> round? half star?); (*) 0 and negative; (*) > 5 (cap?); NULL;
padding with empty stars.

## elapsed(seconds)
Known: 'H:MM:SS' for >= 1 hour.
Open: (*) under one hour ('0:01:40' or '1:40'?); (*) >= 24 hours (days?); 0; negative; fractional
seconds; NULL.

## grade_point(letter)
Known: B+ 3.3, C 2.0, D 1.0.
Open: (*) A+ (4.0 or 4.3), A-, F, D-; (*) lowercase / spaces; unknown letter ('E', 'Z', '');
NULL.

## credit_band(score)
Known: 600 'fair', 760 'very good', 820 'exceptional' (looks FICO-like).
Open: (*) exact boundaries (580/670/740/800?) and which side; (*) bands below fair ('poor'?) and
between fair and very good ('good'?); scores outside 300..850; NULL; fractional.

## color_hex(r, g, b)
Known: lowercase '#rrggbb', zero-padded.
Open: (*) values > 255 and < 0 (clamp, NULL, error?); fractional (round/truncate); NULL.

## vowels(s)
Known: counts a e i o u in lowercase words; 'y' not counted ('swarm' = 1 is consistent).
Open: (*) uppercase vowels; (*) 'y'; empty string; NULL; accented letters; digits.

## next_bizday(date)
Known: Mon..Thu -> next day.
Open: (*) Friday, Saturday, Sunday -> Monday?; (*) public holidays (New Year, Christmas, July 4);
month / year rollover; invalid date; NULL.

## loyalty_pts(amount, years)
Known: years 0 and 1 earn 1 point per unit (100,0 -> 100; 50,1 -> 50).
Open: (*) years thresholds where a multiplier starts (2, 3, 5, 10?); (*) fractional amounts
(floor/round); (*) negative amount; zero; NULL; very large years (cap?).

## mode_val(x)  (aggregate)
Known: most frequent REAL value.
Open: (*) ties (smallest, largest, first seen?); (*) NULLs ignored or counted; all-NULL / empty
input; text values; mixed int / real.

## Budget split
One question for each of the 20 functions first (20). The remaining 10 go where thresholds or
formulas are hidden: band, credit_band, loyalty_pts, shipping get the first extras; the rest are
decided from the answers (see "What the answers taught" below).

## What the answers taught (all 30 questions spent; tests are `tests/visible/<fn>_qNN.json`)
Split: credit_band 3, loyalty_pts 3; band, shipping, abbrev, stars, vowels, next_bizday 2 each;
the other 12 functions 1 each.

- discount: tier is case-insensitive ('GOLD' = gold); unknown tier -> price unchanged as REAL
  (100 -> 100.0); result rounded to 2 decimals (19.99 silver -> 17.99).
- shipping: whole kg, fractional weight rounded UP (2.5 kg national = 3 kg = 14).
  Cost = base + 2 per kg: local 3+2w, national 8+2w, intl 23+2w (intl 2 -> 27, 5 -> 33).
  Weight 0 -> 0. Unknown zone -> NULL. No heavy surcharge (30 kg national -> 68).
- abbrev: len(s) <= n -> s unchanged ('abcd',4 -> 'abcd'; '' -> ''); otherwise s[:n-1] + '~',
  trailing spaces kept ('hello world',7 -> 'hello ~'); n < 2 -> NULL even when s fits ('a',1).
- weekday: Mon..Fri are 'Mon','Tue','Wed','Thu','Fri' but WEEKENDS ARE LOWERCASE: 'sat', 'sun'.
  A time part is accepted ('2024-03-09 15:30:00' -> 'sat'); invalid date ('2024-02-30') -> NULL.
- age: Feb 29 birthday is not reached on Feb 28 of a non-leap year (2000-02-29 on 2023-02-28 = 22);
  `on` before `birth` -> NULL; invalid date -> NULL.
- phone_fmt: 11 digits starting with 1 -> '+1 (555) 123-4567'; any other digit count (7, empty)
  -> the text 'invalid'.
- band: x < 0 -> 'neg'; 0 <= x < 10 -> 'low' (0 and 9.9 are low); 10..50 -> 'mid' (10 and 50 are
  mid); > 50 -> 'high' (51 is high).
- roman: 0 -> 'N'; > 3999 -> NULL (4000); fractional rounded to nearest (3.7 -> 'IV').
- ordinal: teens and x11..x13 take 'th' (13th, 112th); negative -> NULL.
- split_part: idx past the end -> NULL; idx 0 -> whole string; negative idx counts from the end
  (-1 -> last field).
- median3: compares with SQLite ordering: NULL sorts lowest (5, NULL, 1 -> 1), text compares as
  text ('10','9','2' -> '2', type kept), mixed int/real fine (2.5, 1, 4 -> 2.5).
- stars: rounded to the nearest half star; a half is '+' (3.5 -> '***+', 3.2 -> '***',
  3.8 -> '****'); capped at 5; 0 and negative -> ''.
- elapsed: 'H:MM:SS' with hours unpadded even under an hour (100 -> '0:01:40'); a day or more ->
  'Nd H:MM:SS' (90000 -> '1d 1:00:00'); negative -> '<n>s' ('-5s').
- grade_point: case-insensitive; A+ = 4.0 (capped), A- = 3.7; unknown letter 'E' -> 0.0.
- credit_band: FICO bands: < 580 'poor', 580-669 'fair', 670-739 'good', 740-799 'very good',
  800+ 'exceptional' (739 good, 669 fair, 579 poor, 800 exceptional, 799.5 very good: no rounding);
  out of range (900, 250) -> the text 'invalid'.
- color_hex: components clamped to 0..255 (300 -> ff, -10 -> 00); fractional rounded (127.6 -> 80).
- vowels: case-insensitive a e i o u; 'y' counts only at the END of a word ('yummy' 2,
  'rhythm' 0, 'kayak' 2, 'happy day' 4); NULL -> NULL.
- next_bizday: skips Saturday, Sunday and the holidays Dec 25 and Jan 1 (Fri -> Mon, Sat -> Mon,
  12-24 -> 12-26, 12-31 -> next 01-02). July 4 and Thanksgiving are business days; Dec 26 too.
- loyalty_pts: multiplier by years: 0-1 (and negative years) x1, 2-4 x1.5, 5+ x2; amount floored
  first, product floored (9.9 at 2 years -> 9*1.5 = 13.5 -> 13; 9.9 at 0 years -> 9);
  negative amount -> 0.
- mode_val: NULLs ignored; ties go to the SMALLEST value (2,2,5,5,1,1 -> 1); all NULL -> NULL.

## Still uncertain (not asked)
- NULL arguments for most scalar functions (assume NULL -> NULL; only vowels confirmed), and
  NULL tier / NULL zone interactions (discount(100, NULL): 100.0 like an unknown tier, or NULL?).
- band at 50.5 (rule is "> 50" or ">= 51"?); credit_band exact range limits (300 and 850 inclusive?)
  and 'poor' between 300 and 579.
- discount: negative price, surrounding spaces in the tier (' gold ').
- shipping: negative weight, fractional weight under 1 kg (0.3 -> 1 kg?), zone case/spaces.
- abbrev: NULL / negative n (n < 2 suggests NULL).
- weekday/age/next_bizday: NULL and non-date text ('hello', '') - invalid dates gave NULL.
- phone_fmt: NULL, letters, 11 digits not starting with 1, '+1' prefix with spaces.
- roman negative (probably NULL), 3999; ordinal 0 ('0th' or NULL?), fractional.
- split_part: separator absent, empty separator, multi-char separator, empty fields.
- median3: is NULL "lowest" or 0? (NULL, -5, 3 would tell); two NULLs.
- stars: exactly 3.25 / 3.75 (rounding direction at the quarter).
- elapsed: 0, exactly 86400, fractional seconds, large negative ('-3700s'?).
- grade_point: 'F', 'D-', other unknown text ('Z', '') -> 0.0 or NULL?, NULL.
- color_hex: NULL components, 0.5 rounding (banker's or half-up).
- vowels: uppercase 'Y' at word end, accented vowels, punctuation ending a word ('sky!').
- next_bizday: other holidays not probed (e.g. Jan 1 / Dec 25 falling on a weekend: observed date?).
- mode_val: text values, ties between int and real, mixed types.
