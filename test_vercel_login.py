from playwright.sync_api import sync_playwright

def test_login():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            ignore_https_errors=True
        )
        page = context.new_page()
        
        print("Navigating to login page...")
        page.goto("https://supplychain-plum.vercel.app/login.html")
        
        print("Entering credentials...")
        page.fill("#loginEmail", "testuser99@test.com")
        page.fill("#loginPassword", "Test1234!")
        
        # Listen for the login API response to inspect cookies
        with page.expect_response("**/api/login") as response_info:
            page.click("#loginBtn")
            
        login_response = response_info.value
        print(f"Login Response Status: {login_response.status}")
        print(f"Login Response Headers: {login_response.headers}")
        
        print(f"Cookies after login: {context.cookies()}")
        
        print("Waiting for dashboard redirect...")
        page.wait_for_url("**/dashboard")
        print(f"Current URL: {page.url}")
        
        print("Waiting for KPI API call...")
        with page.expect_response("**/api/kpis") as kpi_resp_info:
            pass
        kpi_response = kpi_resp_info.value
        
        print(f"KPI Response Status: {kpi_response.status}")
        # print the request headers for the KPI call to see if cookies were sent
        print(f"KPI Request Headers: {kpi_response.request.headers}")
        
        browser.close()

if __name__ == "__main__":
    test_login()
