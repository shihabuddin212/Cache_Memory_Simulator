# Cache Memory Simulator

A Python program that simulates different cache memory architectures and replacement policies.

## Features

- **Cache Types**:
  - Direct Mapped Cache
  - Fully Associative Cache
  - Set Associative Cache

- **Replacement Policies**:
  - Least Recently Used (LRU)
  - First In, First Out (FIFO)

- **Visualization**:
  - Cache hit/miss visualization
  - Performance comparison between different cache configurations
  - Statistics display

## Requirements

- Python 3.6+
- NumPy
- Matplotlib

## Usage

Run the script:

```
python cache_memory_simulator.py
```

You will be presented with two options:

1. **Run demo with predefined access patterns** - Shows performance of different cache configurations with sequential, random, and loop access patterns
2. **Interactive simulation** - Allows you to configure a cache and test it with custom memory address inputs

### Interactive Mode

In interactive mode, you'll be prompted to:

1. Enter cache size (bytes)
2. Enter block size (bytes)
3. Choose cache type (direct/fully/set)
4. If applicable, choose replacement policy (LRU/FIFO)
5. If set-associative, enter associativity level

Then you can enter memory addresses to access, one at a time. Enter 'stats' to view current statistics or 'q' to quit and see final results.

## Example

```
$ python cache_memory_simulator.py
Cache Memory Simulator
----------------------
1. Run demo with predefined access patterns
2. Interactive simulation

Enter your choice (1/2): 2

Enter cache size (bytes): 256
Enter block size (bytes): 16
Choose cache type (direct/fully/set): set
Enter associativity: 4
Choose replacement policy (LRU/FIFO): LRU

Cache simulator ready. Enter memory addresses to access.
Enter 'q' to quit, 'stats' to view statistics.

Enter memory address: 100
Address 100: Miss
Enter memory address: 104
Address 104: Miss
Enter memory address: 100
Address 100: Hit
Enter memory address: stats
Cache Type: SetAssociativeCache
Cache Size: 256 bytes
Block Size: 16 bytes
Replacement Policy: LRU
Accesses: 3
Hits: 1
Misses: 2
Hit Ratio: 0.3333
Enter memory address: q

Final statistics:
Cache Type: SetAssociativeCache
Cache Size: 256 bytes
Block Size: 16 bytes
Replacement Policy: LRU
Accesses: 3
Hits: 1
Misses: 2
Hit Ratio: 0.3333
```

## How It Works

The simulator models a cache memory with configurable parameters. When a memory address is accessed:

1. The address is converted to a block address by dividing by the block size
2. Depending on the cache type, it determines if the block is in the cache:
   - Direct mapped: Only one possible cache location for each memory block
   - Fully associative: Memory block can be placed anywhere in the cache
   - Set associative: Memory block can be placed in a specific set of the cache
3. If the block is found (cache hit), the hit counter is incremented
4. If not found (cache miss), the block is added to the cache according to the replacement policy
5. Statistics are updated and visualizations reflect the access patterns

## Architecture Details

### Direct Mapped Cache
- Each memory block maps to exactly one cache location
- No replacement policy needed

### Fully Associative Cache
- A memory block can be placed anywhere in the cache
- Requires a replacement policy (LRU or FIFO) to determine which block to replace when the cache is full

### Set Associative Cache
- Combines direct mapped and fully associative approaches
- Cache is divided into sets, and a memory block maps to a specific set
- Within the set, blocks can be placed in any way according to the replacement policy 