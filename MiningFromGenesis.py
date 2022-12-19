
import time
import hashlib
import json_canonical
import json
import pyopencl as cl
import sys

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

    TARGET = "00000daf00000000000000000000000000000000000000000000000000000000"
    EXPECTED_TRIES = (16 ** 5) * (16 / 3) * (16 / 11) * (16 / 15) # not sure if this is correct, but enough for estimating

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
        self.current_hash_rate = 0
        time_offset_for_nonce = int(time.time()) * (10 ** 52)
        print(f"Time offset for nonce: {time_offset_for_nonce}, type {type(time_offset_for_nonce)}")
        MiningFromGenesis.START_NONCE = hex(int("4206900000000000000000000000000000000000000000000000000000000000", 16) + time_offset_for_nonce)
        print(f"Starting nonce: {MiningFromGenesis.START_NONCE}")
        print(f"Expected tries: {MiningFromGenesis.EXPECTED_TRIES}")

    def start(self, num_blocks = 10):
        #self.load_from_files()
        num_tries = []
        while len(self.blocks) < num_blocks:
            result = self.mine_next_block()
            block = result[0]
            tries = result[1]
            num_tries.append(tries)
            MiningFromGenesis.EXPECTED_TRIES = sum(num_tries) / len(num_tries)
            print(f"Average tries: {MiningFromGenesis.EXPECTED_TRIES}")
            self.blocks.append(block)
            self.save_to_files()

    def mine_next_block(self):
        new_block = self.create_new_block()
        last_time = time.time()
        number_of_tries = int(new_block["nonce"], 16) - int(MiningFromGenesis.START_NONCE, 16)
        while not MiningFromGenesis.is_valid_block(new_block):
            new_block["nonce"] = MiningFromGenesis.increment_nonce(new_block["nonce"])
            number_of_tries = int(new_block["nonce"], 16) - int(MiningFromGenesis.START_NONCE, 16)
            if number_of_tries % MiningFromGenesis.UPDATE_RATE == 0:
                time_now = time.time()
                time_diff = time_now - last_time
                last_time = time_now
                hash_rate = MiningFromGenesis.UPDATE_RATE / time_diff
                self.current_hash_rate = hash_rate
                MiningFromGenesis.update_progress(number_of_tries / MiningFromGenesis.EXPECTED_TRIES, hash_rate)
        return (new_block, number_of_tries)

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
            print(f"\nBlock ID {block_id} is valid")
            return True
        return False

    @staticmethod
    def increment_nonce(nonce):
        return hex(int(nonce, 16) + 1)

    @staticmethod
    def get_id_from_json(object_json):
        return MiningFromGenesis.calculate_hash(json_canonical.canonicalize(object_json))

    # Here you can choose between CPU and GPU
    @staticmethod
    def calculate_hash(block):
        return MiningFromGenesis.calculate_hash_on_cpu(block)
        # return MiningFromGenesis.calculate_hash_on_gpu(block)

    @staticmethod
    def calculate_hash_on_cpu(block):
        return hashlib.sha256(block).digest().hex()

    @staticmethod
    def calculate_hash_on_gpu(block):

        headers = cl.get_cl_header_version()
        print(f"OpenCL headers version: {headers}")

        # Create an OpenCL context and command queue
        ctx = cl.create_some_context()
        queue = cl.CommandQueue(ctx)

        # Set up the input data
        input_data = b"hello world"
        input_data_gpu = cl.Buffer(ctx, cl.mem_flags.READ_ONLY, len(input_data))
        cl.enqueue_copy(queue, input_data_gpu, input_data)

        # Set up the output buffer
        hash_output_gpu = cl.Buffer(ctx, cl.mem_flags.WRITE_ONLY, 32)

        # Write the OpenCL kernel
        kernel = """
        __kernel void mysha(__global const uchar *input, __global uchar *output)
        {
            // Calculate the SHA-256 hash using the OpenCL SHA-256 functions
            uchar hash[32];
            sha256(input, 11, hash);

            // Copy the hash to the output buffer
            for (int i = 0; i < 32; i++)
            {
                output[i] = hash[i];
            }
        }
        """

        # Compile the kernel
        program = cl.Program(ctx, kernel).build()

        # Execute the kernel
        global_size = (1,)
        local_size = (1,)
        program.mysha(queue, global_size, local_size, input_data_gpu, hash_output_gpu)

        # Wait for the kernel to finish executing
        queue.finish()

        # Copy the hash output back to the host
        hash_output = bytearray(32)
        cl.enqueue_copy(queue, hash_output, hash_output_gpu)

        return hash_output.hex()
    
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
    miner.start(100)
    #print(miner.blocks)