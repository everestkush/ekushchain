const EverestKush = require('./index.js');

async function test() {
    const ek = new EverestKush('http://127.0.0.1:5000');
    ek.setApiKey('CHANGE_ME');
    
    console.log('=== EverestKush SDK Test ===\n');
    
    // Test 1: Get stats
    console.log('1. Getting blockchain stats...');
    const stats = await ek.getStats();
    console.log(`   Block height: ${stats.chain_length}`);
    console.log(`   Chain valid: ${stats.chain_valid}\n`);
    
    // Test 2: Create wallet
    console.log('2. Creating new wallet...');
    const wallet = await ek.createWallet();
    console.log(`   Address: ${wallet.address}`);
    console.log(`   Public key: ${wallet.public_key.substring(0, 32)}...`);
    console.log(`   Warning: ${wallet.warning}\n`);
    
    // Test 3: Get balance
    console.log('3. Getting balance...');
    const balance = await ek.getBalance('ekush1public00000000000000000000');
    console.log(`   Balance: ${balance.balance_ekush.toLocaleString()} EKUSH\n`);
    
    // Test 4: Get validators
    console.log('4. Getting validators...');
    const validators = await ek.getValidators();
    console.log(`   Active validators: ${validators.count}/${validators.max_validators}\n`);
    
    // Test 5: Search for block
    console.log('5. Searching for block 0...');
    const search = await ek.search('0');
    console.log(`   Type: ${search.type}`);
    if (search.type === 'block') {
        console.log(`   Block hash: ${search.result.hash.substring(0, 32)}...\n`);
    }
    
    console.log('✅ All SDK tests passed!');
}

test().catch(console.error);
