from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import requests
import base64
import cv2
import numpy as np
from dotenv import load_dotenv
import os
import time

width = 220
height = 60
WEIGHTS = []
TEMPLATE = []
with open('training_data.npy', 'rb') as f:
  WEIGHTS = np.load(f).tolist()
  TEMPLATE = np.load(f).tolist()

def captcha_decode(jpeg_bytes):
  img = cv2.imdecode(np.frombuffer(jpeg_bytes, np.uint8), cv2.IMREAD_COLOR)
  gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
  (thresh, bw) = cv2.threshold(gray_img, 180, 255, cv2.THRESH_BINARY)

  bw_not = cv2.bitwise_not(bw)
  summation = []
  for r in range(1, height-1-10):
    for c in range(1, width-1-8):
      sums = np.sum(bw_not[r:r+10, c:c+8])
      summation.append([r, c, sums])
  summation = np.array(summation)
  sorted_sum = summation[summation[:, 2].argsort()]

  chars = 0
  checked_rows = []
  checked_cols = []
  checked = []
  for index in range(100):
    if chars == 4 or sorted_sum[-1-index, 2] < 255 * 10:
      break
    r = sorted_sum[-1-index, 0]
    c = sorted_sum[-1-index, 1]
    
    if ((np.abs(np.array(checked_cols) - c) < 8) * (np.abs(np.array(checked_rows) - r) < 10)).any():
      continue
    checked_rows.append(r)
    checked_cols.append(c)
    checked.append([r, c])
    chars += 1
  checked = np.array(checked)
  checked = checked[checked[:,1].argsort()]
  result = []
  for char in range(chars):
    r = checked[char, 0]
    c = checked[char, 1]
    predicted = bw[r-1:r+10+1, c-1:c+8+1]
    score = []
    for num in range(10):
      score.append(np.max([np.sum((predicted[ :10,  : 8] == TEMPLATE[num]) * WEIGHTS[num]) / np.sum(TEMPLATE[num]),
                           np.sum((predicted[ :10, 1: 9] == TEMPLATE[num]) * WEIGHTS[num]) / np.sum(TEMPLATE[num]),
                           np.sum((predicted[ :10, 2:10] == TEMPLATE[num]) * WEIGHTS[num]) / np.sum(TEMPLATE[num]),
                           np.sum((predicted[1:11,  : 8] == TEMPLATE[num]) * WEIGHTS[num]) / np.sum(TEMPLATE[num]),
                           np.sum((predicted[1:11, 1: 9] == TEMPLATE[num]) * WEIGHTS[num]) / np.sum(TEMPLATE[num]),
                           np.sum((predicted[1:11, 2:10] == TEMPLATE[num]) * WEIGHTS[num]) / np.sum(TEMPLATE[num]),
                           np.sum((predicted[2:12,  : 8] == TEMPLATE[num]) * WEIGHTS[num]) / np.sum(TEMPLATE[num]),
                           np.sum((predicted[2:12, 1: 9] == TEMPLATE[num]) * WEIGHTS[num]) / np.sum(TEMPLATE[num]),
                           np.sum((predicted[2:12, 2:10] == TEMPLATE[num]) * WEIGHTS[num]) / np.sum(TEMPLATE[num])]
                          )
      )
    result.append(score.index(max(score)))
  result = "".join([str(i) for i in result])
  return result

def open_simaster():
  load_dotenv()
  USERNAME = os.getenv("SIMASTER_USERNAME")
  PASSWORD = os.getenv("SIMASTER_PASSWORD")

  driver = webdriver.Firefox()
  driver.get("https://sso.ugm.ac.id/cas/login?service=http%3A%2F%2Fsimaster.ugm.ac.id%2Fugmfw%2Fsignin_simaster%2Fsignin_proses")
  driver.implicitly_wait(1)
  driver.find_element_by_name("username").send_keys(USERNAME)
  driver.implicitly_wait(1)
  driver.find_element_by_name("password").send_keys(PASSWORD)
  driver.implicitly_wait(1)
  driver.find_element_by_name("submit").click()
  driver.implicitly_wait(1)

  while driver.current_url == "https://simaster.ugm.ac.id/ugmfw/signin_simaster/captcha_verification":
    text = driver.find_element_by_id("captcha-img").get_attribute("innerHTML").split('"')[1].split(',')[1]
    jpeg = base64.b64decode(text)
    captcha_result = captcha_decode(jpeg)

    driver.find_element_by_name("captcha").send_keys(captcha_result)
    driver.find_element_by_name("captcha").send_keys(Keys.ENTER)
    time.sleep(1)

if __name__ == "__main__":
  input("press any key to start")
  try:
    open_simaster()
    print("DONE")
  except Exception as e:
    print(f"Error: {str(e)}")
  input("press any key to exit")
