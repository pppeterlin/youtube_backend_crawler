from playwright.sync_api import sync_playwright
import requests, time

class YoutubeBackendCrawler():
    def __init__(self, target_channel):
        self.channels = {
            # Replace with your channel_name and channel_id
            'media_1': {
                'channel_name': 'CHANNEL_NAME_1', 
                'channel_id':'CHANNEL_ID_1'},
            'media_2': {
                'channel_name': 'CHANNEL_NAME_2', 
                'channel_id':'CHANNEL_ID_2'},
        }
        self.channel_name = self.channels[target_channel]['channel_name']
        self.channel_id = self.channels[target_channel]['channel_id']
        self.browser = None
        self.page = None


    def setup_browser(self, playwright, headless=False):
        """Set up browser and page"""

        self.browser = playwright.chromium.launch(headless=False)  
        self.page = self.browser.new_context().new_page()
        self.page.set_extra_http_headers({
        # 'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Mobile Safari/537.36',
        # 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        # 'Accept-Encoding': 'gzip, deflate, br, zstd',
        # 'Accept-Language': 'zh-TW,zh;q=0.8',
        # 'Cache-Control': 'no-cache',
        # 'Pragma': 'no-cache',
        # 'Sec-Fetch-Dest': 'document',
        # 'Sec-Fetch-Mode': 'navigate',
        # 'Sec-Fetch-Site': 'same-origin',
        # 'Sec-Fetch-User': '?1',
        # 'Upgrade-Insecure-Requests': '1',
        })


    def get_2FA_code(self, api_url, token):
        """Get the verification code sent to phone with API"""

        headers = {
            "Authorization": f"Bearer {token}"
            }
        body = {
            "type":"access"
            }
        try:
            res = requests.post(api_url, headers=headers, json=body)
            _2fa_code = res.json()['code']
            return(_2fa_code)
        except Exception as e:
            print(f"Failed to Get the 2FA(Phone) Code From Cloud Storage: {e}")
        return None


    def login(self, google_account, google_password, phone_number):
        """Login to Youtube Studio"""
        def fill_account():
            self.page.fill('#identifierId', google_account)
            self.page.click('#identifierNext')
            self.page.wait_for_load_state('networkidle')

        def fill_password():
            self.page.fill('input[name="Passwd"]', google_password)
            self.page.click('button:has-text("下一步")')
            self.page.wait_for_load_state('networkidle')

        # 跳轉到Youtube後台
        self.page.goto('https://studio.youtube.com')
        self.page.wait_for_load_state('networkidle')

        # 輸入帳號密碼（可能需要重複登入）
        while True:
            time.sleep(3)
            if self.page.locator('input[name="Passwd"]').count()>0: # Check for password field
                print('enter password')
                fill_password()
            elif self.page.locator('[aria-label="電子郵件地址或電話號碼"]').count()>0:  # Check for account field
                print('enter account')
                fill_account()
            else:
                break  # Exit loop if neither field is present

        # 登入：二步驟驗證，輸入手機號碼 (not always)
        if self.page.locator('div[data-sendmethod="SMS"][data-challengevariant="SMS"]').is_visible():
            sms_verification_locator = self.page.locator('div[data-sendmethod="SMS"]')
            sms_verification_locator.click()
            self.page.wait_for_load_state('networkidle')

            phone_input = self.page.locator('#phoneNumberId')
            phone_input.wait_for(timeout=15000)  # wait for max 15 seconds
            phone_input.fill(phone_number)
            self.page.click('button:has-text("下一步")')
            self.page.wait_for_load_state('networkidle')

        elif self.page.locator('#phoneNumberId').is_visible():
            phone_input = self.page.locator('#phoneNumberId')
            phone_input.wait_for(timeout=15000)  # wait for max 15 seconds
            phone_input.fill(phone_number)
            self.page.click('button:has-text("傳送")')
            self.page.wait_for_load_state('networkidle')

            # Input: Authentication code
            time.sleep(5) # wait for new message received
            _2fa_code = self.get_2FA_code()
            self.page.fill('#idvPin', _2fa_code)
            self.page.click('button:has-text("下一步")')
            self.page.wait_for_load_state('networkidle')

        else:
            pass

        # 進入頻道總覽
        print("Successfully login in.")
        redict_url = 'https://www.youtube.com/account'
        self.page.goto(redict_url, wait_until='networkidle', timeout=30000) # 先進頻道總覽
        # self.page.goto(redict_url) # 
        self.page.wait_for_selector("a[href='/channel_switcher?next=%2Faccount&feature=settings']", timeout=15000)
        self.page.click("a[href='/channel_switcher?next=%2Faccount&feature=settings']")

        # 選擇頻道
        channel_title_selector = f"yt-formatted-string[id='channel-title']:has-text('{self.channel_name}')"
        self.page.set_default_timeout(5000)  # 10 seconds timeout
        self.page.click(channel_title_selector)
        button_selector = "button:has-text('知道了')"
        button = self.page.query_selector(button_selector)
        if button:
            button.click()
            print('click success')
        # self.page.wait_for_load_state('networkidle')


    def switch_channel(self, new_channel_name):
        self.channel_name = self.channels[new_channel_name]['channel_name']
        self.channel_id = self.channels[new_channel_name]['channel_id']
        
        # 進入頻道總覽
        redict_url = 'https://www.youtube.com/account'
        self.page.goto(redict_url, wait_until='networkidle', timeout=30000)
        self.page.wait_for_selector("a[href='/channel_switcher?next=%2Faccount&feature=settings']", timeout=15000)
        self.page.click("a[href='/channel_switcher?next=%2Faccount&feature=settings']")

        # 選擇頻道
        channel_title_selector = f"yt-formatted-string[id='channel-title']:has-text('{self.channel_name}')"
        self.page.set_default_timeout(10000)  # 10 seconds timeout
        self.page.click(channel_title_selector)

        # 點擊OK (not always)
        button_locators = [
                'button[aria-label="我知道了"]',
                'button[aria-label="OK"]',
                'button[aria-label="Got it"]'
            ]
        for locator in button_locators:
            if self.page.locator(locator).count() > 0:  # Check if the button exists
                # print(f'Button found: {locator}. Clicking it now.')
                self.page.locator(locator).click()

        self.page.wait_for_load_state('networkidle', timeout=10000)  # Wait for the network to be idle

        # 點擊菜單欄
        self.page.wait_for_selector('#avatar-btn', state='visible', timeout=10000)  # Wait up to 10 seconds for the button to appear
        self.page.click('#avatar-btn')

        # 切換到Youtube Studio
        dashboard_button_locator = 'a#endpoint[href="/dashboard"]'
        self.page.wait_for_selector(dashboard_button_locator, timeout=10000)
        dashboard_button = self.page.locator(dashboard_button_locator)

        if dashboard_button.count() > 0:  
            dashboard_button.click()
        else:
            print('dashboard button no find')
            studio_button_selector = 'a#endpoint[href="https://studio.youtube.com/"]'
            studio_button = self.page.locator(studio_button_selector)
            studio_button.click()

        self.page.wait_for_selector('#menu-item-0', state='visible', timeout=10000) # wait for the studio page loaded


    def get_unique_viewers(self):
        """抓取非重複觀眾人數"""

        url = f'https://studio.youtube.com/channel/{self.channel_id}/analytics/tab-build_audience/period-minus_1_month' #截止至上個月
        # self.page.goto(url, wait_until='networkidle', timeout=30000)
        self.page.goto(url)
        button_selector = 'a.button.continue-to-studio.black-secondary' #繼續使用網頁版工作室
        button = self.page.query_selector(button_selector)
        if button:
            button.click()
        # self.page.wait_for_load_state('networkidle', timeout=30000)

        unique_viewers_locator = self.page.locator(
            'div.metric-container:has-text("非重複觀眾人數") .metric-value, '
            'div.metric-container:has-text("Unique viewers") .metric-value, '
            'div.metric-container:has-text("ユニーク視聴者数") .metric-value'
        ).first
        unique_viewers = unique_viewers_locator.text_content(timeout=30000).strip()
        unique_viewers = int(unique_viewers.replace(',', ''))

        print(f'非重複觀眾數(截止至上個月): {unique_viewers}')
        return(unique_viewers)


    def get_channel_subscribers(self):
        """抓取即時訂閱人數""" 

        url = f'https://studio.youtube.com/channel/{self.channel_id}/analytics/tab-overview/period-default'
        # self.page.goto(url, wait_until='networkidle', timeout=30000)
        self.page.goto(url)
        button_selector = 'a.button.continue-to-studio.black-secondary' #繼續使用網頁版工作室
        button = self.page.query_selector(button_selector)
        if button:
            button.click()
        # self.page.wait_for_load_state('networkidle')
        channel_subscribers = self.page.locator('.metric-value.style-scope.yta-latest-activity-card').first.text_content(timeout=30000)
        channel_subscribers = int(channel_subscribers.replace(',', ''))

        print(f'即時訂閱人數: {channel_subscribers}')
        return(channel_subscribers)


    def get_channel_members(self):
        """抓取頻道付費會員數"""

        url = f'https://studio.youtube.com/channel/{self.channel_id}/monetization/memberships'
        self.page.goto(url, wait_until='networkidle', timeout=30000)
        self.page.wait_for_selector('li#total-sponsors-card')
        channel_members = self.page.locator('li#total-sponsors-card p.total').text_content(timeout=30000)
        channel_members = int(channel_members.replace(',', ''))

        print(f'頻道付費會員數: {channel_members}')
        return(channel_members)


    def logout(self):
        self.browser.close()
