from eth_account import Account
from eth_account.messages import encode_typed_data
from eth_utils import keccak

# 1. Use the exact same private key string from your C++ code
# (Remove the 0x prefix because eth_account expects a raw hex string or bytes)
pk_hex = "0x4c0883a69102937d6231471b5dbb6204fe5129617fc4b10850c416460fae24d7"
# 2. Replicate the eip712_data JSON structure exactly
domain = {
    "chainId": 42161,
    "name": "Exchange",
    "verifyingContract": "0x0000000000000000000000000000000000000000",
    "version": "1"
}

message = {
    "source": "https://hyperliquid.xyz",
    "connectionId": "0x1111111111111111111111111111111111111111111111111111111111111111"
}

# 3. Explicitly define the types schema matching the C++ layout
types = {
    "Agent": [
        {"name": "source", "type": "string"},
        {"name": "connectionId", "type": "bytes32"}
    ]
}

# 4. Compile the data into a SignableMessage container
signable = encode_typed_data(domain_data=domain, message_types=types, message_data=message)

# 5. Calculate the final 32-byte digest (EIP-191 ribbon hash)
final_digest = keccak(b"\x19\x01" + signable.header + signable.body)

# 6. Sign the message using the private key2
signed = Account.sign_message(signable, private_key=pk_hex)

# 7. Print outputs to compare with C++ Console
print("--- Python Output ---")
print(f"Domain Hash:  0x{signable.header.hex()}")
print(f"Message Hash: 0x{signable.body.hex()}")
print(f"Final Digest: 0x{final_digest.hex()}")
print(f"R:            0x{hex(signed.r)[2:].zfill(64)}")
print(f"S:            0x{hex(signed.s)[2:].zfill(64)}")
print(f"V:            {signed.v}")