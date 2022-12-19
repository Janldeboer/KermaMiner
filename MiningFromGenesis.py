
import time
import hashlib
import json_canonical
import json

class MiningFromGenesis:

    GENESIS_BLOCK = {
      "T": "00000002af000000000000000000000000000000000000000000000000000000" ,
      "created": 1624219079,
      "miner" : "dionyziz",
      "nonce": "0000000000000000000000000000000000000000000000000000002634878840",
      "note" : "The Economist 2021-06-20: Crypto-miners are probably to blame for the graphics-chip shortage" ,
      "previd" : None,
      "txids" : [],
      "type" : "block"
    }

    TARGET = "00000002af000000000000000000000000000000000000000000000000000000"

    START_NONCE = "4206900000000000000000000000000000000000000000000000000000000000"

    MAX_NONCE = "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"

    PUBLIC_KEY = "6690a9f3e28f961532289de1835556bbb6dac5fdba43b7f8bf00fcbdbe1795a7"
    
    FILE_NAME_BLOCKS = "blocks.json"
    FILE_NAME_COINBASE = "coinbase.json"

    UPDATE_RATE = 20000

    def __init__(self):
        self.blocks = [MiningFromGenesis.GENESIS_BLOCK]
        self.coinbase_transactions = []
        self.current_height = 1
        time_offset_for_nonce = int(time.time()) * (10 ** 52)
        print(f"Time offset for nonce: {time_offset_for_nonce}, type {type(time_offset_for_nonce)}")
        MiningFromGenesis.START_NONCE = hex(int("4206900000000000000000000000000000000000000000000000000000000000", 16) + time_offset_for_nonce)
        print(f"Starting nonce: {MiningFromGenesis.START_NONCE}")

    def start(self, num_blocks = 10):
        self.load_from_files()
        while len(self.blocks) < num_blocks:
            self.blocks.append(self.mine_next_block())
            self.save_to_files()

    def mine_next_block(self):
        new_block = self.create_new_block()
        last_time = time.time()
        while not MiningFromGenesis.is_valid_block(new_block):
            new_block["nonce"] = MiningFromGenesis.increment_nonce(new_block["nonce"])
            # print every 100000 tries
            number_of_tries = int(new_block["nonce"], 16) - int(MiningFromGenesis.START_NONCE, 16)
            if number_of_tries % MiningFromGenesis.UPDATE_RATE == 0:
                time_now = time.time()
                time_diff = time_now - last_time
                last_time = time_now
                print(f"Block {len(self.blocks)}: {number_of_tries} tries, hash rate: {round(hash_rate)} hashes per second")
        return new_block
                hash_rate = MiningFromGenesis.UPDATE_RATE / time_diff

    def create_new_block(self):
      prev_block_id = MiningFromGenesis.get_id_from_json(self.blocks[-1])
      self.create_coinbase_tx()
      coinbase_tx_id = MiningFromGenesis.get_id_from_json(self.coinbase_transactions[-1])
      return {
            "type": "block",
            "txids": [coinbase_tx_id],
            "nonce": MiningFromGenesis.START_NONCE,
            "miner": "group 6 will rule",
            "note": f"Block {len(self.blocks)}, group 6 will rule",
            "previd": prev_block_id,
            "created": time.time(),
            "T": MiningFromGenesis.TARGET
        }
      
    def create_coinbase_tx(self):
      if len(self.blocks) > len(self.coinbase_transactions):
        reward = 5 * (10 ** 12)
        coinbase_tx = {
              "type": "transaction",
              "height": len(self.blocks),
              "outputs": [
                {
                  "value": reward,
                  "pubkey": MiningFromGenesis.PUBLIC_KEY
                }
              ]
        }
        self.coinbase_transactions.append(coinbase_tx)

    def load_from_files(self):
        with open(MiningFromGenesis.FILE_NAME_BLOCKS, "r") as f:
            self.blocks = json.load(f)
        with open(MiningFromGenesis.FILE_NAME_COINBASE, "r") as f:
            self.coinbase_transactions = json.load(f)

    def save_to_files(self):
        with open(MiningFromGenesis.FILE_NAME_BLOCKS, "w") as f:
            json.dump(self.blocks, f, indent=4)
        with open(MiningFromGenesis.FILE_NAME_COINBASE, "w") as f:
            json.dump(self.coinbase_transactions, f, indent=4)

    @staticmethod
    def is_valid_block(block):
        block_id = MiningFromGenesis.get_id_from_json(block)
        if int(block_id, 16) <= int(block["T"], 16):
            print(f"Block ID {block_id} is valid")
            return True
        return False

    @staticmethod
    def increment_nonce(nonce):
        return hex(int(nonce, 16) + 1)

    @staticmethod
    def get_id_from_json(object_json):
        return hashlib.sha256(json_canonical.canonicalize(object_json)).digest().hex()
    @staticmethod
    def update_progress(progress, hash_rate):
      # Add T, M, G, etc. to hash rate, depending on how big it is
      if hash_rate < 10 ** 3:
          hash_rate_str = f"{round(hash_rate)} H/s"
      elif hash_rate < 10 ** 6:
          hash_rate_str = f"{round(hash_rate / 10 ** 3)} KH/s"
      elif hash_rate < 10 ** 9:
          hash_rate_str = f"{round(hash_rate / 10 ** 6)} MH/s"
      elif hash_rate < 10 ** 12:
          hash_rate_str = f"{round(hash_rate / 10 ** 9)} GH/s"
      else:
          hash_rate_str = f"{round(hash_rate / 10 ** 12)} TH/s"

      hash_rate_str = hash_rate_str.rjust(9)

      bar_length = 40
      if isinstance(progress, int):
          progress = float(progress)
      if not isinstance(progress, float):
          progress = 0
      if progress < 0:
          progress = 0
      cleaned_progress = progress
      if progress >= 1:
          cleaned_progress = 1

      block = int(round(bar_length * cleaned_progress))
      # also make sure that the percentage always takes up 5 characters
      percentage_str = "{0:.1f}%".format(progress * 100).rjust(6)

      # calculate time estimate
      time_estimate = (1 - progress) * (MiningFromGenesis.EXPECTED_TRIES / hash_rate)
      prefix = " "
      if time_estimate < 0:
          time_estimate = time_estimate * -1
          prefix = "-"
      time_estimate_seconds = int(time_estimate) % 60
      time_estimate_minutes = int(time_estimate / 60) % 60
      time_estimate_hours = int(time_estimate / 3600)
      time_estimate_str = prefix + f"{time_estimate_hours:02d}:{time_estimate_minutes:02d}:{time_estimate_seconds:02d}"

      text = "Progress: [{0}] {1} {2} {3}\r".format( "#" * block + "-" * (bar_length - block), percentage_str, hash_rate_str, time_estimate_str)
      sys.stdout.write(text)
      sys.stdout.flush()


if __name__ == "__main__":
    miner = MiningFromGenesis()
    miner.start(1000)
    #print(miner.blocks)