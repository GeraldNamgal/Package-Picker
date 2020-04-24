"""
Functional tests for the web service using Selenium
"""

from sys import platform
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from django.test import LiveServerTestCase
from pyvirtualdisplay import Display


class LoginTest(LiveServerTestCase):
    """
    Selenium tests for the web service
    """

    # Needed to overwrite LiveServerTestCase default port (i.e. 8001)
    port = 8000

    def setUp(self):

        # Create chrome sessions depending on OS
        if platform == "win32":
            path = "C:\\DRIVERS\\chromedriver_win32\\chromedriver.exe"
            self.driver = webdriver.Chrome(executable_path=path)
        elif platform == "darwin":
            path = "/usr/local/bin/chromedriver"
            self.driver = webdriver.Chrome(executable_path=path)
        else:

            # Assure no visibility display for Ubuntu CLI to render without UI
            # Assure large enough screen to preven responsive look which hides some buttons
            display = Display(visible=0, size=(1920, 1080))
            display.start()

            path = "/usr/bin/chromedriver"
            self.driver = webdriver.Chrome(executable_path=path)

        self.driver.implicitly_wait(3)

        self.driver.maximize_window()
        self.driver.get(self.live_server_url)
        super(LoginTest, self).setUp()

    def tearDown(self):
        self.driver.quit()
        super(LoginTest, self).tearDown()

    def test_work_process(self):
        """
        End to end test of the recommendation workflow
        """

        # get the login buttons
        login_button = self.driver.find_element_by_xpath(
            "//*[@id='navbarBasicExample']/div[2]/div/div")

        login_button.click()

        # Check if the user redirected back to the main page
        self.assertEqual('http://localhost:8000/', self.driver.current_url)

        # About button
        about_ele = self.driver.find_element_by_xpath(
            "//*[@id='navbarBasicExample']/div[1]/a[2]")
        about_ele.click()

        # Check if the user at about page
        self.assertEqual('http://localhost:8000/about', self.driver.current_url)

        # My repositories button
        reps_ele_path = "//*[@id='navbarBasicExample']/div[1]/a[3]"
        reps_ele = self.driver.find_element_by_xpath(reps_ele_path)
        reps_ele.click()

        # Check if the user at my repositories page
        self.assertEqual('http://localhost:8000/repositories', self.driver.current_url)

        # The first element from the repos list
        first_repo_ele = self.driver.find_element_by_xpath(
            "//tbody/tr[1]/td[1]/a")
        first_repo_ele.click()

        # Check if the user at recommendations page
        self.assertEqual("Recommendations", self.driver.title)
        loading_state = self.driver.find_element_by_xpath("//*[@class='dataTables_empty']")
        self.assertEqual("Loading...", loading_state.get_attribute('textContent'))

        # Wait for data to load
        WebDriverWait(self.driver, 30).until(EC.invisibility_of_element(loading_state))

        # Check if text in branch selector is `master`
        branch_span = self.driver.find_element_by_xpath("//*[@class='dropdown-trigger']/button/span")
        self.assertEqual("master", branch_span.get_attribute('textContent'))

        # Click on dropdown and another branch in the Dropdown
        branch_to_click = self.driver.find_element_by_xpath("//*[@class='dropdown-menu']/div/a[@href='?branch=test']")
        branch_dropdown = self.driver.find_element_by_xpath("//*[@class='dropdown-trigger']/button")
        branch_dropdown.click()
        branch_to_click.click()

        # Assure that we are looking at another branch
        branch_span = self.driver.find_element_by_xpath("//*[@class='dropdown-trigger']/button/span")
        self.assertEqual("test", branch_span.get_attribute('textContent'))

        # Check that we're loading data for the new branch
        loading_state = self.driver.find_element_by_xpath("//*[@class='dataTables_empty']")
        self.assertEqual("Loading...", loading_state.get_attribute('textContent'))

        # Wait for data to load
        WebDriverWait(self.driver, 30).until(EC.invisibility_of_element(loading_state))

        # Category border
        category_order_ele = self.driver.find_element_by_xpath(
            "//*[@id='recommendTable']/thead/tr/th[4]")

        # Click it twice to make sure the first recommendation has at least one category
        category_order_ele.click()
        category_order_ele.click()

        # The first category
        first_category_ele = self.driver.find_element_by_xpath(
            "//*[@id='recommendTable']/tbody/tr[1]/td[4]/div[1]/button")
        first_category_ele.click()

        # Clear button
        clear_ele = self.driver.find_element_by_xpath("//*[@id='categoryClear']")
        clear_ele.click()

        # Filter text inputs
        search_ele_path = "//*[@id='recommendationFilter']"
        search_ele = self.driver.find_element_by_xpath(search_ele_path)
        search_ele.send_keys("te")
        search_ele.clear()

        # The first element from the recommendation list
        first_recommendation_ele = self.driver.find_element_by_xpath(
            "//*[@id='recommendTable']/tbody/tr/td[2]/a")
        first_recommendation_ele.click()

        # Verify that we're on npmjs.com
        self.assertRegex(self.driver.title, r'npm')

        # Go back to the recommendations page
        self.driver.back()

        # Wait for the data to load
        loading_state = self.driver.find_element_by_xpath("//*[@class='dataTables_empty']")
        self.assertEqual("Loading...", loading_state.get_attribute('textContent'))
        WebDriverWait(self.driver, 30).until(EC.invisibility_of_element(loading_state))

        # Logout button
        logout_ele = self.driver.find_element_by_xpath(
            "//*[@id='navbarBasicExample']/div[2]/div/div")
        logout_ele.click()

        # Check if the user redirected back to the main page
        self.assertEqual("Package Picker", self.driver.title)