// tron-demo/src/jlabi.js

export const comptrollerAbi = [
    // Minimal ABI with the functions you use
    {
      "inputs": [],
      "name": "getAllMarkets",
      "outputs": [
        { "internalType": "address[]", "name": "", "type": "address[]" }
      ],
      "stateMutability": "view",
      "type": "function"
    }
  ];
  
  export const jTokenAbi = [
    {
      "inputs": [],
      "name": "symbol",
      "outputs": [{ "internalType": "string", "name": "", "type": "string" }],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [],
      "name": "supplyRatePerBlock",
      "outputs": [{ "internalType": "uint256", "name": "", "type": "uint256" }],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [],
      "name": "borrowRatePerBlock",
      "outputs": [{ "internalType": "uint256", "name": "", "type": "uint256" }],
      "stateMutability": "view",
      "type": "function"
    }
  ];
  