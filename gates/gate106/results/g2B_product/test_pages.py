import pathlib, re
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
    inputs = re.findall(r'<input[^>]*>', page('signup.html'))
    assert len([i for i in inputs if 'required' in i]) < 5
def test_signup_no_bank_or_gst():
    s = page('signup.html')
    for f in ('name="gst"', 'name="account"', 'name="ifsc"', 'name="pan"'):
        assert f not in s
def test_dashboard_links_to_deals():
    assert 'deals.html' in page('dashboard.html')
def test_dashboard_not_empty():
    assert 'No data.' not in page('dashboard.html')
def test_nav_links_to_deals():
    for n in ('dashboard.html', 'deals.html', 'invite.html'):
        nav = re.search(r'<nav>.*?</nav>', page(n), re.S).group(0)
        assert 'href="deals.html"' in nav and 'Deals' in nav
def test_apply_buttons_submit():
    assert page('deals.html').count('action="applied.html"') >= 3
def test_applied_page_exists():
    a = page('applied.html')
    assert 'You applied to' in a and 'deal' in a and 'href="deals.html"' in a and '7 days' in a
def test_deals_mentions_payment():
    assert '7 days' in page('deals.html')
def test_home_links_signup_above_footer():
    s = page('index.html')
    assert 'signup.html' in s.split('<footer')[0]
def test_home_creator_block():
    s = page('index.html')
    top = s.split('About us')[0]
    assert 'Get paid by Indian brands' in top and '₹1,500' in top and '₹3,000' in top
    assert '7 days' in top and 'no GST' in top and '₹8,000' in top and 'Join as a creator' in top
