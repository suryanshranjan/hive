import pathlib
D = pathlib.Path(__file__).parent
page = lambda n: (D / n).read_text(encoding='utf-8')
def test_pages_exist():
    for n in ('index.html', 'signup.html', 'dashboard.html', 'deals.html', 'invite.html', 'terms.html'):
        assert (D / n).exists()
def test_signup_collects_email_and_instagram():
    s = page('signup.html'); assert 'name="email"' in s and 'name="instagram"' in s
def test_signup_goes_to_dashboard():
    assert 'dashboard.html' in page('signup.html')
def test_deals_listed():
    assert page('deals.html').count('<li') >= 3
def test_invite_reward_is_500():
    assert '₹500' in page('invite.html')
def test_signup_is_short():
    s = page('signup.html')
    for f in ('gst', 'pan', 'account', 'ifsc', 'address'):
        assert f'name="{f}"' not in s
    assert s.count('required') <= 4
def test_home_has_creator_cta():
    import re
    s = page('index.html')
    assert re.search(r'<a\b[^>]*class="cta"[^>]*href="signup.html"|<a\b[^>]*href="signup.html"[^>]*class="cta"', s)
    assert '₹' in s
    assert 'New creators earn about ₹8,000 a month' in s
def test_invite_reachable_and_visible():
    import re
    d = page('dashboard.html')
    assert 'href="invite.html"' in d and 'href="deals.html"' in d
    assert 'No data.' not in d
    s = page('invite.html')
    assert 'margin-top:400px' not in s
    assert '₹500' in re.search(r'<h1>(.*?)</h1>', s, re.S).group(1)
    assert 'wa.me' in s
