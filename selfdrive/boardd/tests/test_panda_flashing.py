#!/usr/bin/env python3
import selfdrive.boardd.boardd as boardd
from panda import *
import unittest
import time
import os

from panda import BASEDIR as PANDA_BASEDIR

def get_firmware_fn():
  signed_fn = os.path.join(PANDA_BASEDIR, "board", "obj", "panda.bin.signed")
  if os.path.exists(signed_fn):
    return signed_fn
  else:
    fn = "obj/panda.bin"
    build_st(fn, clean=False)
    return os.path.join(PANDA_BASEDIR, "board", fn)


def get_expected_signature():
  try:
    return Panda.get_signature_from_firmware(get_firmware_fn())
  except Exception:
    return b""

class TestPandaFlashing(unittest.TestCase):
  def setUp(self):
    print("Setting up panda before the test")
    panda = None
    panda_dfu = PandaDFU.list()
    if len(panda_dfu) > 0:
      panda_dfu = PandaDFU(panda_dfu[0])
      panda_dfu.recover()
      time.sleep(1)

    panda_list = Panda.list()
    if len(panda_list) > 0:
      panda = Panda(panda_list[0])
    else:
      print("Panda setup failed")
      raise AssertionError

    fw_signature = get_expected_signature()

    panda_signature = b"" if panda.bootstub else panda.get_signature()

    if panda.bootstub or panda_signature != fw_signature:
      panda.flash(get_firmware_fn())

    if panda.bootstub:
      panda.recover()


  def test_panda_flashing(self):
    # Ensure we have one normal panda running
    pandas = Panda.list()
    self.assertEqual(len(pandas), 1)
    # Ensure it is running the firmware
    panda1 = Panda(pandas[0])
    time.sleep(5)
    self.assertFalse(panda1.bootstub)
    # Move the panda into the DFU mode
    panda1.reset(enter_bootstub=True)
    panda1.reset(enter_bootloader=True)
    print("DFU?")
    time.sleep(5)
    # Ensure no normal pandas and one DFU panda
    self.assertEqual(len(PandaDFU.list()), 1)
    self.assertEqual(len(Panda.list()), 0)
    # Run the C++ panda flasher, takes a bit of time
    os.system("export BASEDIR=\"/home/batman/openpilot/\"; ./fix_panda")
    # Now we should have one panda and 0 DFU pandas
    self.assertEqual(len(Panda.list()), 1)
    self.assertEqual(len(PandaDFU.list()), 0)
    print("Test 1 finished")

  def test_release_bootloader(self):
    # Ensure we have one normal panda running
    pandas = Panda.list()
    self.assertEqual(len(pandas), 1)
    # Flash release bootloader and firmware
    os.system("git clone https://github.com/commaai/panda-artifacts.git; cd panda-artifacts; python flash.py")
    # Now we should flash the development firmware, find it doesn't run due to the signature and reflash the dev bootloader and firmware
    os.system("export BASEDIR=\"/home/batman/openpilot/\"; ./fix_panda")
    # Cleanup
    os.system("rm -rf panda-artifacts")
    # In the end we want no DFU pandas and one running panda
    self.assertEqual(len(PandaDFU.list()), 0)
    self.assertEqual(len(Panda.list()), 1)
    panda1 = Panda(pandas[0])
    self.assertFalse(panda1.bootstub)
    print("Test 2 finished")

  def test_signed_firmware(self):
    # We make the same preparation as on previous test
    pandas = Panda.list()
    self.assertEqual(len(pandas), 1)
    os.system("git clone https://github.com/commaai/panda-artifacts.git; cd panda-artifacts; python flash.py")
    os.system("ls; rm -rf panda-artifacts")
    # We load the signed firmware
    os.system("cd ../../../panda/board/obj/; wget \"https://github.com/commaai/openpilot/blob/release2/panda/board/obj/panda.bin.signed?raw=true\" -O panda.bin.signed")
    # Run the panda flasher. It should install the signed firmware
    os.system("export BASEDIR=\"/home/batman/openpilot/\"; ./fix_panda")
    # In the end we want no DFU pandas and one running panda
    self.assertEqual(len(PandaDFU.list()), 0)
    self.assertEqual(len(Panda.list()), 1)
    panda1 = Panda(pandas[0])
    self.assertFalse(panda1.bootstub)
    print("Test 3 finished")

if __name__ == '__main__':
    unittest.main()
