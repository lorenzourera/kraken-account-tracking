# test.sh
#!/bin/bash

echo "🧪 Running Iteration 1 Tests..."
echo ""

echo "1️⃣ Testing connection..."
python cli.py test-connection || exit 1

echo ""
echo "2️⃣ Pulling balance..."
python cli.py pull-balance || exit 1

echo ""
echo "3️⃣ Showing balance..."
python cli.py show-balance || exit 1

echo ""
echo "4️⃣ Checking history..."
python cli.py history --limit 5 || exit 1

echo ""
echo "5️⃣ Listing accounts..."
python cli.py list-accounts || exit 1

echo ""
echo "✅ All tests passed!"