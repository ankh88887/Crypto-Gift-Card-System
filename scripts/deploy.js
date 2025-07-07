const hre = require("hardhat");

async function main() {
  console.log("Deploying GiftCard contract...");

  // Get the contract factory
  const GiftCard = await hre.ethers.getContractFactory("GiftCard");

  // Deploy the contract
  const giftCard = await GiftCard.deploy();

  // Wait for deployment to complete
  await giftCard.deployed();

  console.log("GiftCard contract deployed to:", giftCard.address);
  console.log("Network:", hre.network.name);
  
  // Save the contract address for easy access
  console.log("\n=== IMPORTANT ===");
  console.log("Copy this contract address to your wepage/app.js file:");
  console.log(`const CONTRACT_ADDRESS = '${giftCard.address}';`);
  console.log("=================\n");
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });