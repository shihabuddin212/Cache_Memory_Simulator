import numpy as np
import matplotlib.pyplot as plt
from collections import deque, OrderedDict
import tkinter as tk
from tkinter import ttk, messagebox, StringVar
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

# Cell 1: Cache Memory Simulator Classes

class CacheSimulator:
    """Base class for cache memory simulator"""
    
    def __init__(self, cache_size, block_size, replacement_policy="LRU"):
        """
        Initialize cache simulator
        
        Parameters:
        - cache_size: Cache size in bytes
        - block_size: Cache block/line size in bytes
        - replacement_policy: 'LRU' or 'FIFO'
        """
        self.cache_size = cache_size
        self.block_size = block_size
        self.replacement_policy = replacement_policy
        self.hits = 0
        self.misses = 0
        self.access_count = 0
        self.access_history = []
        
        # Enhanced statistics
        self.hit_streaks = []  # Track consecutive hits
        self.miss_streaks = []  # Track consecutive misses
        self.current_streak = {'type': None, 'count': 0}
        self.hot_addresses = {}  # Track frequently accessed addresses
        self.cold_addresses = set()  # Track addresses accessed only once
    
    def access(self, address):
        """Access memory at the given address"""
        self.access_count += 1
        hit = self._check_hit(address)
        
        # Update hit/miss count
        if hit:
            self.hits += 1
            result = "Hit"
            # Update streak
            if self.current_streak['type'] == 'hit':
                self.current_streak['count'] += 1
            else:
                if self.current_streak['type'] == 'miss' and self.current_streak['count'] > 0:
                    self.miss_streaks.append(self.current_streak['count'])
                self.current_streak = {'type': 'hit', 'count': 1}
        else:
            self.misses += 1
            result = "Miss"
            # Update streak
            if self.current_streak['type'] == 'miss':
                self.current_streak['count'] += 1
            else:
                if self.current_streak['type'] == 'hit' and self.current_streak['count'] > 0:
                    self.hit_streaks.append(self.current_streak['count'])
                self.current_streak = {'type': 'miss', 'count': 1}
        
        # Track address frequency
        self.hot_addresses[address] = self.hot_addresses.get(address, 0) + 1
        if self.hot_addresses[address] == 1:
            self.cold_addresses.add(address)
        elif address in self.cold_addresses:
            self.cold_addresses.remove(address)
        
        self.access_history.append((address, result))
        return result
    
    def _check_hit(self, address):
        """Check if address is in cache (to be implemented by subclasses)"""
        raise NotImplementedError
    
    def get_hit_ratio(self):
        """Calculate and return the hit ratio"""
        if self.access_count == 0:
            return 0
        return self.hits / self.access_count
    
    def get_miss_ratio(self):
        """Calculate and return the miss ratio"""
        if self.access_count == 0:
            return 0
        return self.misses / self.access_count
    
    def get_avg_hit_streak(self):
        """Calculate average hit streak length"""
        if not self.hit_streaks:
            return 0
        return sum(self.hit_streaks) / len(self.hit_streaks)
    
    def get_avg_miss_streak(self):
        """Calculate average miss streak length"""
        if not self.miss_streaks:
            return 0
        return sum(self.miss_streaks) / len(self.miss_streaks)
    
    def get_hot_addresses(self, threshold=3):
        """Get addresses accessed more than threshold times"""
        return {addr: count for addr, count in self.hot_addresses.items() 
                if count >= threshold}
    
    def reset_stats(self):
        """Reset hit/miss statistics"""
        self.hits = 0
        self.misses = 0
        self.access_count = 0
        self.access_history = []
        self.hit_streaks = []
        self.miss_streaks = []
        self.current_streak = {'type': None, 'count': 0}
        self.hot_addresses = {}
        self.cold_addresses = set()
    
    def get_stats_text(self):
        """Return cache statistics as text"""
        stats = []
        stats.append(f"Cache Type: {self.__class__.__name__}")
        stats.append(f"Cache Size: {self.cache_size} bytes")
        stats.append(f"Block Size: {self.block_size} bytes")
        stats.append(f"Replacement Policy: {self.replacement_policy}")
        stats.append(f"Accesses: {self.access_count}")
        stats.append(f"Hits: {self.hits}")
        stats.append(f"Misses: {self.misses}")
        stats.append(f"Hit Ratio: {self.get_hit_ratio():.4f}")
        stats.append(f"Miss Ratio: {self.get_miss_ratio():.4f}")
        
        # Add enhanced statistics
        if self.hit_streaks:
            stats.append(f"Avg Hit Streak: {self.get_avg_hit_streak():.2f}")
        if self.miss_streaks:
            stats.append(f"Avg Miss Streak: {self.get_avg_miss_streak():.2f}")
        
        hot_addrs = self.get_hot_addresses(threshold=5)
        if hot_addrs:
            stats.append(f"Hot Addresses: {len(hot_addrs)}")
        
        stats.append(f"Unique Addresses: {len(self.hot_addresses)}")
        
        return "\n".join(stats)
    
    def get_advanced_stats(self):
        """Return detailed statistics as a dictionary"""
        return {
            "cache_type": self.__class__.__name__,
            "cache_size": self.cache_size,
            "block_size": self.block_size,
            "replacement_policy": self.replacement_policy,
            "accesses": self.access_count,
            "hits": self.hits,
            "misses": self.misses,
            "hit_ratio": self.get_hit_ratio(),
            "miss_ratio": self.get_miss_ratio(),
            "avg_hit_streak": self.get_avg_hit_streak(),
            "avg_miss_streak": self.get_avg_miss_streak(),
            "hot_addresses_count": len(self.get_hot_addresses(threshold=3)),
            "unique_addresses": len(self.hot_addresses),
            "cold_addresses": len(self.cold_addresses)
        }


class DirectMappedCache(CacheSimulator):
    """Direct-mapped cache implementation"""
    
    def __init__(self, cache_size, block_size):
        super().__init__(cache_size, block_size)
        self.num_blocks = cache_size // block_size
        self.cache = [-1] * self.num_blocks  # -1 represents an empty block
        self.tags = [-1] * self.num_blocks
    
    def _check_hit(self, address):
        block_address = address // self.block_size
        cache_index = block_address % self.num_blocks
        tag = block_address // self.num_blocks
        
        if self.tags[cache_index] == tag:
            return True
        else:
            self.cache[cache_index] = block_address
            self.tags[cache_index] = tag
            return False


class FullyAssociativeCache(CacheSimulator):
    """Fully associative cache implementation"""
    
    def __init__(self, cache_size, block_size, replacement_policy="LRU"):
        super().__init__(cache_size, block_size, replacement_policy)
        self.num_blocks = cache_size // block_size
        
        if replacement_policy == "LRU":
            # Using OrderedDict for LRU functionality
            self.cache = OrderedDict()
        elif replacement_policy == "FIFO":
            # Using regular dict for storage and deque for FIFO tracking
            self.cache = {}
            self.queue = deque()
        else:
            raise ValueError("Unsupported replacement policy")
    
    def _check_hit(self, address):
        block_address = address // self.block_size
        
        if self.replacement_policy == "LRU":
            if block_address in self.cache:
                # Move accessed item to the end (most recently used)
                self.cache.move_to_end(block_address)
                return True
            else:
                if len(self.cache) >= self.num_blocks:
                    # Remove least recently used item (first item)
                    self.cache.popitem(last=False)
                self.cache[block_address] = True
                return False
                
        elif self.replacement_policy == "FIFO":
            if block_address in self.cache:
                return True
            else:
                if len(self.cache) >= self.num_blocks:
                    # Remove the oldest entry (FIFO)
                    oldest = self.queue.popleft()
                    del self.cache[oldest]
                self.cache[block_address] = True
                self.queue.append(block_address)
                return False


class SetAssociativeCache(CacheSimulator):
    """Set associative cache implementation"""
    
    def __init__(self, cache_size, block_size, associativity, replacement_policy="LRU"):
        super().__init__(cache_size, block_size, replacement_policy)
        self.associativity = associativity
        self.num_blocks = cache_size // block_size
        self.num_sets = self.num_blocks // associativity
        
        # Initialize cache sets
        self.sets = []
        for _ in range(self.num_sets):
            if replacement_policy == "LRU":
                self.sets.append(OrderedDict())
            elif replacement_policy == "FIFO":
                self.sets.append({"cache": {}, "queue": deque()})
            else:
                raise ValueError("Unsupported replacement policy")
    
    def _check_hit(self, address):
        block_address = address // self.block_size
        set_index = block_address % self.num_sets
        tag = block_address // self.num_sets
        
        if self.replacement_policy == "LRU":
            cache_set = self.sets[set_index]
            if tag in cache_set:
                # Move accessed item to the end (most recently used)
                cache_set.move_to_end(tag)
                return True
            else:
                if len(cache_set) >= self.associativity:
                    # Remove least recently used item (first item)
                    cache_set.popitem(last=False)
                cache_set[tag] = block_address
                return False
                
        elif self.replacement_policy == "FIFO":
            cache_set = self.sets[set_index]["cache"]
            queue = self.sets[set_index]["queue"]
            
            if tag in cache_set:
                return True
            else:
                if len(cache_set) >= self.associativity:
                    # Remove the oldest entry (FIFO)
                    oldest = queue.popleft()
                    del cache_set[oldest]
                cache_set[tag] = block_address
                queue.append(tag)
                return False

# Cell 2: Visualization Functions

def create_access_pattern_figure(cache, title=None):
    """Create figure for memory access pattern visualization with enhanced hit/miss display"""
    fig = Figure(figsize=(8, 6))
    
    # Create a grid of subplots
    gs = fig.add_gridspec(2, 2, height_ratios=[3, 1])
    ax1 = fig.add_subplot(gs[0, :])  # Access pattern plot (top row)
    ax2 = fig.add_subplot(gs[1, 0])  # Hit/Miss ratio (bottom left)
    ax3 = fig.add_subplot(gs[1, 1])  # Hit/Miss count (bottom right)
    
    addresses = [x[0] for x in cache.access_history]
    results = [1 if x[1] == "Hit" else 0 for x in cache.access_history]
    
    if not addresses:  # No data yet
        ax1.text(0.5, 0.5, "No memory accesses yet", 
                ha='center', va='center', transform=ax1.transAxes)
        return fig
    
    # Access pattern plot
    scatter = ax1.scatter(range(len(addresses)), addresses, c=results, 
                        cmap='coolwarm', marker='o', s=50, alpha=0.7)
    
    # Add a running hit ratio line
    cumulative_hits = np.cumsum(results)
    hit_ratios = [sum(results[:i+1])/(i+1) if i > 0 else results[0] for i in range(len(results))]
    
    ax1_twin = ax1.twinx()
    ax1_twin.plot(range(len(hit_ratios)), hit_ratios, 'g-', alpha=0.7, linewidth=2)
    ax1_twin.set_ylabel('Running Hit Ratio', color='g')
    ax1_twin.tick_params(axis='y', labelcolor='g')
    ax1_twin.set_ylim(0, 1.1)
    
    cbar = fig.colorbar(scatter, ax=ax1, ticks=[0, 1])
    cbar.set_label('Cache Result')
    cbar.set_ticklabels(['Miss', 'Hit'])
    
    ax1.set_xlabel('Access Sequence')
    ax1.set_ylabel('Memory Address')
    ax1.set_title(title or f'Cache Access Pattern ({cache.__class__.__name__}, {cache.replacement_policy})')
    ax1.grid(True, linestyle='--', alpha=0.7)
    
    # Hit/Miss ratio pie chart
    hit_ratio = cache.get_hit_ratio()
    miss_ratio = 1 - hit_ratio
    
    ax2.pie([hit_ratio, miss_ratio], labels=['Hit', 'Miss'], autopct='%1.1f%%', 
            colors=['green', 'red'], startangle=90, wedgeprops=dict(width=0.5))
    ax2.set_title('Hit/Miss Ratio')
    
    # Hit/Miss count bar chart
    ax3.bar(['Hits', 'Misses'], [cache.hits, cache.misses], color=['green', 'red'])
    ax3.set_title('Hit/Miss Count')
    for i, v in enumerate([cache.hits, cache.misses]):
        ax3.text(i, v/2, str(v), ha='center', va='center', color='white', fontweight='bold')
    
    # Add overall stats at the bottom
    stats_text = f'Accesses: {cache.access_count}   Hits: {cache.hits}   Misses: {cache.misses}   Hit Ratio: {hit_ratio:.4f}'
    fig.text(0.5, 0.01, stats_text, ha='center', fontsize=10)
    
    fig.tight_layout()
    return fig

def create_comparison_figure(results):
    """Create figure for cache performance comparison with enhanced metrics"""
    fig = Figure(figsize=(10, 8))
    
    # Create a grid of subplots
    gs = fig.add_gridspec(2, 2)
    ax1 = fig.add_subplot(gs[0, 0])  # Hit ratio plot (top left)
    ax2 = fig.add_subplot(gs[0, 1])  # Miss ratio plot (top right)
    ax3 = fig.add_subplot(gs[1, :])  # Combined plot (bottom)
    
    names = [r["Config"] for r in results]
    hit_ratios = [r["Hit Ratio"] for r in results]
    miss_ratios = [1 - hr for hr in hit_ratios]
    
    # Hit ratio bar chart
    bars1 = ax1.bar(names, hit_ratios, color='green')
    ax1.set_xlabel('Cache Configuration')
    ax1.set_ylabel('Hit Ratio')
    ax1.set_title('Hit Ratio Comparison')
    ax1.set_ylim(0, 1)
    ax1.set_xticklabels(names, rotation=45, ha='right')
    
    for i, v in enumerate(hit_ratios):
        ax1.text(i, v + 0.02, f'{v:.4f}', ha='center')
    
    # Miss ratio bar chart
    bars2 = ax2.bar(names, miss_ratios, color='red')
    ax2.set_xlabel('Cache Configuration')
    ax2.set_ylabel('Miss Ratio')
    ax2.set_title('Miss Ratio Comparison')
    ax2.set_ylim(0, 1)
    ax2.set_xticklabels(names, rotation=45, ha='right')
    
    for i, v in enumerate(miss_ratios):
        ax2.text(i, v + 0.02, f'{v:.4f}', ha='center')
    
    # Combined stacked bar chart
    x = np.arange(len(names))
    width = 0.35
    
    ax3.bar(x, hit_ratios, width, label='Hit Ratio', color='green')
    ax3.bar(x, miss_ratios, width, bottom=hit_ratios, label='Miss Ratio', color='red')
    
    ax3.set_xlabel('Cache Configuration')
    ax3.set_ylabel('Ratio')
    ax3.set_title('Combined Hit/Miss Ratio')
    ax3.set_xticks(x)
    ax3.set_xticklabels(names, rotation=45, ha='right')
    ax3.legend()
    
    fig.tight_layout()
    return fig

# Add a new function for detailed hit/miss visualization
def create_hit_miss_timeline(cache):
    """Create a timeline visualization of hits and misses"""
    fig = Figure(figsize=(10, 6))
    ax = fig.add_subplot(111)
    
    # Extract data
    addresses = [x[0] for x in cache.access_history]
    results = [1 if x[1] == "Hit" else 0 for x in cache.access_history]
    
    if not addresses:  # No data yet
        ax.text(0.5, 0.5, "No memory accesses yet", 
                ha='center', va='center', transform=ax.transAxes)
        return fig
    
    # Plot hit/miss timeline
    colors = ['red' if res == 0 else 'green' for res in results]
    ax.bar(range(len(results)), [1] * len(results), color=colors, width=0.8)
    
    # Add running hit ratio line
    cumulative_hits = np.cumsum(results)
    hit_ratios = [sum(results[:i+1])/(i+1) if i > 0 else results[0] for i in range(len(results))]
    
    ax_twin = ax.twinx()
    ax_twin.plot(range(len(hit_ratios)), hit_ratios, 'b-', linewidth=2)
    ax_twin.set_ylabel('Running Hit Ratio', color='b')
    ax_twin.tick_params(axis='y', labelcolor='b')
    ax_twin.set_ylim(0, 1.1)
    
    ax.set_xlabel('Access Sequence')
    ax.set_ylabel('Cache Result')
    ax.set_title(f'Hit/Miss Timeline ({cache.__class__.__name__}, {cache.replacement_policy})')
    ax.set_yticks([0.5])
    ax.set_yticklabels(['Access'])
    ax.set_ylim(0, 1)
    
    # Add a legend
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='green', label='Hit'),
        Patch(facecolor='red', label='Miss')
    ]
    ax.legend(handles=legend_elements, loc='upper left')
    
    fig.tight_layout()
    return fig

# Cell 3: Cache Simulation Logic

def test_cache(cache, addresses):
    """Test cache with a sequence of memory addresses"""
    cache.reset_stats()
    results = []
    
    for addr in addresses:
        result = cache.access(addr)
        results.append(result)
    
    return results

def compare_cache_performance(cache_configs, access_pattern):
    """Compare performance of different cache configurations"""
    results = []
    
    for config in cache_configs:
        cache_type = config["type"]
        cache_size = config["cache_size"]
        block_size = config["block_size"]
        policy = config.get("policy", "LRU")
        associativity = config.get("associativity", 1)
        
        if cache_type == "DirectMapped":
            cache = DirectMappedCache(cache_size, block_size)
        elif cache_type == "FullyAssociative":
            cache = FullyAssociativeCache(cache_size, block_size, policy)
        elif cache_type == "SetAssociative":
            cache = SetAssociativeCache(cache_size, block_size, associativity, policy)
        else:
            raise ValueError(f"Unknown cache type: {cache_type}")
        
        test_cache(cache, access_pattern)
        
        results.append({
            "Config": f"{cache_type} ({policy if cache_type != 'DirectMapped' else 'N/A'})",
            "Hit Ratio": cache.get_hit_ratio(),
            "Cache": cache
        })
    
    return results

# Cell 4: Main GUI Application

class CacheSimulatorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        
        self.title("Cache Memory Simulator")
        self.geometry("1000x700")
        self.minsize(1000, 700)
        
        self.create_widgets()
        
        self.interactive_cache = None
        self.demo_results = None
        self.access_patterns = {}  # Store multiple access patterns
    
    def create_widgets(self):
        # Create notebook (tabbed interface)
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Interactive simulation tab
        self.interactive_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.interactive_frame, text="Interactive Simulation")
        self.setup_interactive_tab()
        
        # Demo tab
        self.demo_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.demo_frame, text="Demo Mode")
        self.setup_demo_tab()
        
        # Multiple access patterns tab
        self.multi_pattern_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.multi_pattern_frame, text="Multiple Patterns")
        self.setup_multi_pattern_tab()
    
    def setup_interactive_tab(self):
        # Left panel (configuration and controls)
        left_panel = ttk.Frame(self.interactive_frame)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=10, pady=10)
        
        # Configuration frame
        config_frame = ttk.LabelFrame(left_panel, text="Cache Configuration")
        config_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(config_frame, text="Cache Size (bytes):").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.cache_size_var = StringVar(value="256")
        ttk.Entry(config_frame, textvariable=self.cache_size_var, width=10).grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(config_frame, text="Block Size (bytes):").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.block_size_var = StringVar(value="16")
        ttk.Entry(config_frame, textvariable=self.block_size_var, width=10).grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(config_frame, text="Cache Type:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.cache_type_var = StringVar(value="direct")
        cache_types = ttk.Combobox(config_frame, textvariable=self.cache_type_var, width=15)
        cache_types['values'] = ("direct", "fully", "set")
        cache_types.grid(row=2, column=1, padx=5, pady=5)
        cache_types.bind('<<ComboboxSelected>>', self.on_cache_type_changed)
        
        # Associativity (initially hidden)
        self.assoc_label = ttk.Label(config_frame, text="Associativity:")
        self.assoc_var = StringVar(value="4")
        self.assoc_entry = ttk.Entry(config_frame, textvariable=self.assoc_var, width=10)
        
        # Replacement policy
        self.policy_label = ttk.Label(config_frame, text="Replacement Policy:")
        self.policy_var = StringVar(value="LRU")
        self.policy_combo = ttk.Combobox(config_frame, textvariable=self.policy_var, width=15)
        self.policy_combo['values'] = ("LRU", "FIFO")
        
        # Initialize cache button
        ttk.Button(config_frame, text="Initialize Cache", command=self.initialize_interactive_cache).grid(
            row=5, column=0, columnspan=2, padx=5, pady=10)
        
        # Memory access frame
        access_frame = ttk.LabelFrame(left_panel, text="Memory Access")
        access_frame.pack(fill=tk.X, padx=5, pady=10)
        
        ttk.Label(access_frame, text="Memory Address:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.address_var = StringVar()
        self.address_entry = ttk.Entry(access_frame, textvariable=self.address_var, width=10)
        self.address_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Button(access_frame, text="Access", command=self.access_memory).grid(
            row=1, column=0, padx=5, pady=5)
        ttk.Button(access_frame, text="Reset", command=self.reset_interactive_cache).grid(
            row=1, column=1, padx=5, pady=5)
        
        # Custom sequence frame - new addition
        custom_frame = ttk.LabelFrame(left_panel, text="Custom Sequence")
        custom_frame.pack(fill=tk.X, padx=5, pady=10)
        
        ttk.Label(custom_frame, text="Enter Addresses:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.sequence_var = StringVar()
        sequence_entry = ttk.Entry(custom_frame, textvariable=self.sequence_var, width=25)
        sequence_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(custom_frame, text="(Space separated, e.g., '1 2 3 4 2 3 6 7')").grid(
            row=1, column=0, columnspan=2, sticky=tk.W, padx=5, pady=2)
        
        ttk.Button(custom_frame, text="Process Sequence", command=self.process_custom_sequence).grid(
            row=2, column=0, columnspan=2, padx=5, pady=5)
        
        # Enhanced batch access
        ttk.Label(access_frame, text="Batch Size:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.batch_size_var = StringVar(value="10")
        ttk.Entry(access_frame, textvariable=self.batch_size_var, width=10).grid(row=2, column=1, padx=5, pady=5)
        
        ttk.Label(access_frame, text="Pattern:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        self.batch_pattern_var = StringVar(value="sequential")
        batch_pattern_combo = ttk.Combobox(access_frame, textvariable=self.batch_pattern_var, width=15)
        batch_pattern_combo['values'] = ("sequential", "random", "loop", "stride", "reverse", "locality")
        batch_pattern_combo.grid(row=3, column=1, padx=5, pady=5)
        
        ttk.Button(access_frame, text="Batch Access", command=self.batch_access).grid(
            row=4, column=0, columnspan=2, padx=5, pady=5)
        
        # Statistics frame
        self.stats_frame = ttk.LabelFrame(left_panel, text="Statistics")
        self.stats_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.stats_text = tk.Text(self.stats_frame, width=30, height=10, wrap=tk.WORD)
        self.stats_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.stats_text.insert(tk.END, "Initialize a cache to see statistics")
        self.stats_text.config(state=tk.DISABLED)
        
        # Access history frame
        history_frame = ttk.LabelFrame(left_panel, text="Access History")
        history_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.history_text = tk.Text(history_frame, width=30, height=10, wrap=tk.WORD)
        self.history_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Right panel (visualization)
        self.interactive_right_panel = ttk.Frame(self.interactive_frame)
        self.interactive_right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        vis_frame = ttk.LabelFrame(self.interactive_right_panel, text="Visualization")
        vis_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Initial empty figure
        self.interactive_fig = Figure(figsize=(5, 4))
        self.interactive_ax = self.interactive_fig.add_subplot(111)
        self.interactive_ax.text(0.5, 0.5, "Initialize a cache and access memory to see visualization", 
                ha='center', va='center', transform=self.interactive_ax.transAxes)
        
        self.interactive_canvas = FigureCanvasTkAgg(self.interactive_fig, master=vis_frame)
        self.interactive_canvas.draw()
        self.interactive_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def setup_demo_tab(self):
        # Control panel
        control_frame = ttk.Frame(self.demo_frame)
        control_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Access pattern selection
        ttk.Label(control_frame, text="Access Pattern:").pack(side=tk.LEFT, padx=(0, 5))
        self.pattern_var = StringVar(value="sequential")
        pattern_combo = ttk.Combobox(control_frame, textvariable=self.pattern_var, width=15)
        pattern_combo['values'] = ("sequential", "random", "loop", "stride", "reverse", "locality")
        pattern_combo.pack(side=tk.LEFT, padx=5)
        
        # Run demo button
        ttk.Button(control_frame, text="Run Demo", command=self.run_demo).pack(side=tk.LEFT, padx=10)
        
        # Results notebook (tabbed interface for demo results)
        self.demo_notebook = ttk.Notebook(self.demo_frame)
        self.demo_notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Comparison tab
        self.comparison_frame = ttk.Frame(self.demo_notebook)
        self.demo_notebook.add(self.comparison_frame, text="Performance Comparison")
        
        # Detailed view tab
        self.detail_frame = ttk.Frame(self.demo_notebook)
        self.demo_notebook.add(self.detail_frame, text="Detailed View")
        
        # Hit/Miss Ratio tab (New)
        self.hit_miss_frame = ttk.Frame(self.demo_notebook)
        self.demo_notebook.add(self.hit_miss_frame, text="Hit/Miss Ratio")
        
        # Initial empty comparison figure
        self.comparison_fig = Figure(figsize=(6, 4))
        ax = self.comparison_fig.add_subplot(111)
        ax.text(0.5, 0.5, "Run demo to see comparison results", 
                ha='center', va='center', transform=ax.transAxes)
        
        self.comparison_canvas = FigureCanvasTkAgg(self.comparison_fig, master=self.comparison_frame)
        self.comparison_canvas.draw()
        self.comparison_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Initial empty detail figure
        self.detail_fig = Figure(figsize=(6, 4))
        ax = self.detail_fig.add_subplot(111)
        ax.text(0.5, 0.5, "Run demo to see detailed view", 
                ha='center', va='center', transform=ax.transAxes)
        
        self.detail_canvas = FigureCanvasTkAgg(self.detail_fig, master=self.detail_frame)
        self.detail_canvas.draw()
        self.detail_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Initial empty hit/miss ratio figure
        self.hit_miss_fig = Figure(figsize=(6, 4))
        ax = self.hit_miss_fig.add_subplot(111)
        ax.text(0.5, 0.5, "Run demo to see hit/miss ratio analysis", 
                ha='center', va='center', transform=ax.transAxes)
        
        self.hit_miss_canvas = FigureCanvasTkAgg(self.hit_miss_fig, master=self.hit_miss_frame)
        self.hit_miss_canvas.draw()
        self.hit_miss_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def setup_multi_pattern_tab(self):
        # Control panel
        control_frame = ttk.Frame(self.multi_pattern_frame)
        control_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Left panel - Access pattern configuration
        left_panel = ttk.LabelFrame(self.multi_pattern_frame, text="Access Patterns")
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=10, pady=10, ipadx=10, ipady=10)
        
        # Pattern selection 
        pattern_frame = ttk.Frame(left_panel)
        pattern_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(pattern_frame, text="Available Patterns:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.multi_pattern_var = StringVar(value="sequential")
        pattern_combo = ttk.Combobox(pattern_frame, textvariable=self.multi_pattern_var, width=15)
        pattern_combo['values'] = ("sequential", "random", "loop", "stride", "reverse", "locality")
        pattern_combo.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(pattern_frame, text="Number of Accesses:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.multi_accesses_var = StringVar(value="100")
        ttk.Entry(pattern_frame, textvariable=self.multi_accesses_var, width=10).grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(pattern_frame, text="Pattern Name:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.pattern_name_var = StringVar(value="pattern1")
        ttk.Entry(pattern_frame, textvariable=self.pattern_name_var, width=15).grid(row=2, column=1, padx=5, pady=5)
        
        ttk.Button(pattern_frame, text="Generate Pattern", command=self.generate_pattern).grid(
            row=3, column=0, columnspan=2, padx=5, pady=5)
        
        # Pattern list
        ttk.Label(left_panel, text="Generated Patterns:").pack(anchor=tk.W, padx=5, pady=5)
        self.patterns_listbox = tk.Listbox(left_panel, width=30, height=8)
        self.patterns_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        pattern_buttons = ttk.Frame(left_panel)
        pattern_buttons.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(pattern_buttons, text="Remove Pattern", command=self.remove_pattern).pack(side=tk.LEFT, padx=5)
        ttk.Button(pattern_buttons, text="Clear All", command=self.clear_patterns).pack(side=tk.RIGHT, padx=5)
        
        # Cache configuration
        cache_frame = ttk.LabelFrame(left_panel, text="Cache Configuration")
        cache_frame.pack(fill=tk.X, padx=5, pady=10)
        
        ttk.Label(cache_frame, text="Cache Type:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.multi_cache_type_var = StringVar(value="all")
        cache_type_combo = ttk.Combobox(cache_frame, textvariable=self.multi_cache_type_var, width=15)
        cache_type_combo['values'] = ("all", "direct", "fully", "set")
        cache_type_combo.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Button(left_panel, text="Run Comparison", command=self.run_multi_pattern_comparison).pack(
            fill=tk.X, padx=10, pady=10)
        
        # Right panel - Results
        right_panel = ttk.Frame(self.multi_pattern_frame)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Results notebook
        self.multi_notebook = ttk.Notebook(right_panel)
        self.multi_notebook.pack(fill=tk.BOTH, expand=True)
        
        # Hit Ratio Comparison tab
        self.hit_ratio_frame = ttk.Frame(self.multi_notebook)
        self.multi_notebook.add(self.hit_ratio_frame, text="Hit Ratio Comparison")
        
        # Miss Ratio Comparison tab
        self.miss_ratio_frame = ttk.Frame(self.multi_notebook)
        self.multi_notebook.add(self.miss_ratio_frame, text="Miss Ratio Comparison")
        
        # Pattern Performance tab
        self.pattern_perf_frame = ttk.Frame(self.multi_notebook)
        self.multi_notebook.add(self.pattern_perf_frame, text="Pattern Performance")
        
        # Initial empty figures
        self.hit_ratio_fig = Figure(figsize=(6, 4))
        ax = self.hit_ratio_fig.add_subplot(111)
        ax.text(0.5, 0.5, "Generate patterns and run comparison to see hit ratio results", 
                ha='center', va='center', transform=ax.transAxes)
        
        self.hit_ratio_canvas = FigureCanvasTkAgg(self.hit_ratio_fig, master=self.hit_ratio_frame)
        self.hit_ratio_canvas.draw()
        self.hit_ratio_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        self.miss_ratio_fig = Figure(figsize=(6, 4))
        ax = self.miss_ratio_fig.add_subplot(111)
        ax.text(0.5, 0.5, "Generate patterns and run comparison to see miss ratio results", 
                ha='center', va='center', transform=ax.transAxes)
        
        self.miss_ratio_canvas = FigureCanvasTkAgg(self.miss_ratio_fig, master=self.miss_ratio_frame)
        self.miss_ratio_canvas.draw()
        self.miss_ratio_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        self.pattern_perf_fig = Figure(figsize=(6, 4))
        ax = self.pattern_perf_fig.add_subplot(111)
        ax.text(0.5, 0.5, "Generate patterns and run comparison to see pattern performance", 
                ha='center', va='center', transform=ax.transAxes)
        
        self.pattern_perf_canvas = FigureCanvasTkAgg(self.pattern_perf_fig, master=self.pattern_perf_frame)
        self.pattern_perf_canvas.draw()
        self.pattern_perf_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def on_cache_type_changed(self, event=None):
        cache_type = self.cache_type_var.get()
        
        # Hide all optional widgets first
        self.assoc_label.grid_forget()
        self.assoc_entry.grid_forget()
        self.policy_label.grid_forget()
        self.policy_combo.grid_forget()
        
        # Show widgets based on cache type
        if cache_type == "direct":
            pass  # No additional widgets needed
        elif cache_type == "fully":
            self.policy_label.grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
            self.policy_combo.grid(row=3, column=1, padx=5, pady=5)
        elif cache_type == "set":
            self.assoc_label.grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
            self.assoc_entry.grid(row=3, column=1, padx=5, pady=5)
            self.policy_label.grid(row=4, column=0, sticky=tk.W, padx=5, pady=5)
            self.policy_combo.grid(row=4, column=1, padx=5, pady=5)
    
    def initialize_interactive_cache(self):
        try:
            cache_size = int(self.cache_size_var.get())
            block_size = int(self.block_size_var.get())
            cache_type = self.cache_type_var.get()
            
            if cache_type == "direct":
                self.interactive_cache = DirectMappedCache(cache_size, block_size)
            elif cache_type == "fully":
                policy = self.policy_var.get()
                self.interactive_cache = FullyAssociativeCache(cache_size, block_size, policy)
            elif cache_type == "set":
                associativity = int(self.assoc_var.get())
                policy = self.policy_var.get()
                self.interactive_cache = SetAssociativeCache(cache_size, block_size, associativity, policy)
            else:
                messagebox.showerror("Error", "Invalid cache type")
                return
            
            self.reset_interactive_cache()
            messagebox.showinfo("Success", "Cache initialized successfully")
            
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid input: {str(e)}")
    
    def reset_interactive_cache(self):
        if self.interactive_cache:
            self.interactive_cache.reset_stats()
            self.update_interactive_stats()
            self.history_text.delete(1.0, tk.END)
            
            # Reset visualization
            self.interactive_fig = create_access_pattern_figure(self.interactive_cache)
            self.interactive_canvas.figure = self.interactive_fig
            self.interactive_canvas.draw()
    
    def access_memory(self):
        if not self.interactive_cache:
            messagebox.showerror("Error", "Please initialize a cache first")
            return
        
        try:
            address = int(self.address_var.get())
            result = self.interactive_cache.access(address)
            
            # Update history
            self.history_text.insert(tk.END, f"Address {address}: {result}\n")
            self.history_text.see(tk.END)
            
            # Update statistics
            self.update_interactive_stats()
            
            # Update visualization
            self.interactive_fig = create_access_pattern_figure(self.interactive_cache)
            self.interactive_canvas.figure = self.interactive_fig
            self.interactive_canvas.draw()
            
        except ValueError:
            messagebox.showerror("Error", "Invalid address. Please enter a number.")
    
    def batch_access(self):
        """Process a batch of memory accesses based on selected pattern"""
        if not self.interactive_cache:
            messagebox.showerror("Error", "Please initialize a cache first")
            return
        
        try:
            batch_size = int(self.batch_size_var.get())
            pattern_type = self.batch_pattern_var.get()
            
            # Generate access pattern
            addresses = self.generate_access_pattern(pattern_type, batch_size)
            
            # Process addresses
            for addr in addresses:
                result = self.interactive_cache.access(addr)
                self.history_text.insert(tk.END, f"Address {addr}: {result}\n")
            
            self.history_text.see(tk.END)
            self.update_interactive_stats()
            
            # Update visualization
            self.interactive_fig = create_access_pattern_figure(self.interactive_cache)
            self.interactive_canvas.figure = self.interactive_fig
            self.interactive_canvas.draw()
            
            messagebox.showinfo("Batch Complete", f"Processed {batch_size} addresses with {pattern_type} pattern")
            
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid input: {str(e)}")
    
    def process_custom_sequence(self):
        """Process a custom sequence of memory addresses"""
        if not self.interactive_cache:
            messagebox.showerror("Error", "Please initialize a cache first")
            return
        
        try:
            # Get the sequence string and split by whitespace
            sequence_str = self.sequence_var.get().strip()
            if not sequence_str:
                messagebox.showerror("Error", "Please enter a sequence of addresses")
                return
                
            # Parse the addresses
            addresses = []
            for addr_str in sequence_str.split():
                addr = int(addr_str)
                addresses.append(addr)
            
            if not addresses:
                messagebox.showerror("Error", "No valid addresses found")
                return
                
            # Process each address
            for addr in addresses:
                result = self.interactive_cache.access(addr)
                self.history_text.insert(tk.END, f"Address {addr}: {result}\n")
            
            self.history_text.see(tk.END)
            self.update_interactive_stats()
            
            # Update visualization
            self.interactive_fig = create_access_pattern_figure(self.interactive_cache)
            self.interactive_canvas.figure = self.interactive_fig
            self.interactive_canvas.draw()
            
            messagebox.showinfo("Sequence Complete", f"Processed {len(addresses)} addresses from custom sequence")
            
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid input: {str(e)}")
    
    def update_interactive_stats(self):
        if self.interactive_cache:
            self.stats_text.config(state=tk.NORMAL)
            self.stats_text.delete(1.0, tk.END)
            self.stats_text.insert(tk.END, self.interactive_cache.get_stats_text())
            self.stats_text.config(state=tk.DISABLED)
    
    def generate_access_pattern(self, pattern_type, size, start_addr=0, max_addr=1000):
        """Generate different memory access patterns"""
        np.random.seed(42)  # For reproducible results
        
        if pattern_type == "sequential":
            # Sequential access
            return list(range(start_addr, start_addr + size * 4, 4))
        
        elif pattern_type == "random":
            # Random access
            return list(np.random.randint(0, max_addr, size) * 4)
        
        elif pattern_type == "loop":
            # Loop pattern
            loop_size = min(size, 25)  # Smaller loop size
            repeats = size // loop_size + (1 if size % loop_size > 0 else 0)
            pattern = []
            for _ in range(repeats):
                pattern.extend(range(start_addr, start_addr + loop_size * 4, 4))
            return pattern[:size]
        
        elif pattern_type == "stride":
            # Strided access pattern (every 16 bytes)
            return list(range(start_addr, start_addr + size * 16, 16))
        
        elif pattern_type == "reverse":
            # Reverse sequential
            return list(range(start_addr + (size-1) * 4, start_addr - 4, -4))
        
        elif pattern_type == "locality":
            # Temporal locality pattern (80% accesses in 20% of address space)
            hot_region_size = max_addr // 5
            pattern = []
            
            for _ in range(size):
                if np.random.random() < 0.8:  # 80% in hot region
                    addr = np.random.randint(0, hot_region_size)
                else:  # 20% in rest of memory
                    addr = np.random.randint(hot_region_size, max_addr)
                pattern.append(addr * 4)
            
            return pattern
        
        else:
            raise ValueError(f"Unknown pattern type: {pattern_type}")
    
    def run_demo(self):
        pattern_type = self.pattern_var.get()
        
        # Generate access pattern
        access_pattern = self.generate_access_pattern(pattern_type, 100)
        
        # Define cache configurations
        configs = [
            {"type": "DirectMapped", "cache_size": 256, "block_size": 16},
            {"type": "FullyAssociative", "cache_size": 256, "block_size": 16, "policy": "LRU"},
            {"type": "FullyAssociative", "cache_size": 256, "block_size": 16, "policy": "FIFO"},
            {"type": "SetAssociative", "cache_size": 256, "block_size": 16, "associativity": 4, "policy": "LRU"},
            {"type": "SetAssociative", "cache_size": 256, "block_size": 16, "associativity": 4, "policy": "FIFO"}
        ]
        
        # Run comparison
        self.demo_results = compare_cache_performance(configs, access_pattern)
        
        # Update comparison visualization
        self.comparison_fig = create_comparison_figure(self.demo_results)
        self.comparison_canvas.figure = self.comparison_fig
        self.comparison_canvas.draw()
        
        # Detailed view of set-associative cache with LRU policy
        set_assoc_cache = SetAssociativeCache(256, 16, 4, "LRU")
        test_cache(set_assoc_cache, access_pattern)
        
        self.detail_fig = create_access_pattern_figure(
            set_assoc_cache, f"Detailed View: Set-Associative (LRU) with {pattern_type} access pattern")
        self.detail_canvas.figure = self.detail_fig
        self.detail_canvas.draw()
        
        # Create hit/miss ratio visualization
        self.hit_miss_fig = self.create_hit_miss_ratio_figure(self.demo_results)
        self.hit_miss_canvas.figure = self.hit_miss_fig
        self.hit_miss_canvas.draw()
        
        messagebox.showinfo("Demo Complete", f"Demo completed with {pattern_type} access pattern")
    
    def create_hit_miss_ratio_figure(self, results):
        """Create a figure showing hit and miss ratios side by side"""
        fig = Figure(figsize=(8, 4))
        ax = fig.add_subplot(111)
        
        names = [r["Config"] for r in results]
        hit_ratios = [r["Hit Ratio"] for r in results]
        miss_ratios = [1 - hr for hr in hit_ratios]
        
        x = np.arange(len(names))
        width = 0.35
        
        ax.bar(x - width/2, hit_ratios, width, label='Hit Ratio', color='green')
        ax.bar(x + width/2, miss_ratios, width, label='Miss Ratio', color='red')
        
        ax.set_xlabel('Cache Configuration')
        ax.set_ylabel('Ratio')
        ax.set_title('Hit vs Miss Ratio Comparison')
        ax.set_xticks(x)
        ax.set_xticklabels(names, rotation=45, ha='right')
        ax.set_ylim(0, 1)
        ax.legend()
        
        for i, v in enumerate(hit_ratios):
            ax.text(i - width/2, v + 0.02, f'{v:.2f}', ha='center', va='bottom', fontsize=8)
            ax.text(i + width/2, miss_ratios[i] + 0.02, f'{miss_ratios[i]:.2f}', ha='center', va='bottom', fontsize=8)
        
        fig.tight_layout()
        return fig
    
    def generate_pattern(self):
        """Generate and store an access pattern for multi-pattern comparison"""
        try:
            pattern_type = self.multi_pattern_var.get()
            num_accesses = int(self.multi_accesses_var.get())
            pattern_name = self.pattern_name_var.get()
            
            if not pattern_name or pattern_name in self.access_patterns:
                messagebox.showerror("Error", "Please provide a unique pattern name")
                return
            
            # Generate the pattern
            pattern = self.generate_access_pattern(pattern_type, num_accesses)
            self.access_patterns[pattern_name] = {
                "type": pattern_type,
                "addresses": pattern,
                "size": num_accesses
            }
            
            # Update the listbox
            self.patterns_listbox.insert(tk.END, f"{pattern_name} ({pattern_type}, {num_accesses} accesses)")
            
            # Clear the name field
            self.pattern_name_var.set("")
            
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid input: {str(e)}")
    
    def remove_pattern(self):
        """Remove the selected pattern from the list"""
        selected = self.patterns_listbox.curselection()
        if not selected:
            messagebox.showinfo("Info", "Please select a pattern to remove")
            return
        
        # Get pattern name from listbox entry
        entry = self.patterns_listbox.get(selected[0])
        pattern_name = entry.split(" (")[0]
        
        # Remove from storage and listbox
        if pattern_name in self.access_patterns:
            del self.access_patterns[pattern_name]
        
        self.patterns_listbox.delete(selected[0])
    
    def clear_patterns(self):
        """Clear all patterns"""
        self.access_patterns = {}
        self.patterns_listbox.delete(0, tk.END)
    
    def run_multi_pattern_comparison(self):
        """Run comparison with multiple patterns"""
        if not self.access_patterns:
            messagebox.showinfo("Info", "Please generate at least one access pattern first")
            return
        
        # Get cache configuration
        cache_type = self.multi_cache_type_var.get()
        
        # Define cache configurations based on selection
        if cache_type == "all":
            configs = [
                {"type": "DirectMapped", "cache_size": 256, "block_size": 16},
                {"type": "FullyAssociative", "cache_size": 256, "block_size": 16, "policy": "LRU"},
                {"type": "SetAssociative", "cache_size": 256, "block_size": 16, "associativity": 4, "policy": "LRU"}
            ]
        elif cache_type == "direct":
            configs = [{"type": "DirectMapped", "cache_size": 256, "block_size": 16}]
        elif cache_type == "fully":
            configs = [
                {"type": "FullyAssociative", "cache_size": 256, "block_size": 16, "policy": "LRU"},
                {"type": "FullyAssociative", "cache_size": 256, "block_size": 16, "policy": "FIFO"}
            ]
        elif cache_type == "set":
            configs = [
                {"type": "SetAssociative", "cache_size": 256, "block_size": 16, "associativity": 4, "policy": "LRU"},
                {"type": "SetAssociative", "cache_size": 256, "block_size": 16, "associativity": 4, "policy": "FIFO"}
            ]
        
        # Run comparisons for each pattern
        multi_results = {}
        for pattern_name, pattern_data in self.access_patterns.items():
            multi_results[pattern_name] = compare_cache_performance(
                configs, pattern_data["addresses"])
        
        # Create visualizations
        self.create_multi_pattern_visualizations(multi_results)
        
        messagebox.showinfo("Complete", "Multi-pattern comparison completed")
    
    def create_multi_pattern_visualizations(self, multi_results):
        """Create visualizations for multi-pattern comparison"""
        # Hit ratio figure
        self.hit_ratio_fig = Figure(figsize=(8, 5))
        ax1 = self.hit_ratio_fig.add_subplot(111)
        
        patterns = list(multi_results.keys())
        configs = [r["Config"] for r in multi_results[patterns[0]]]
        
        x = np.arange(len(patterns))
        width = 0.8 / len(configs)
        
        for i, config in enumerate(configs):
            hit_ratios = [multi_results[p][i]["Hit Ratio"] for p in patterns]
            ax1.bar(x + i*width - 0.4 + width/2, hit_ratios, width, label=config)
        
        ax1.set_xlabel('Access Pattern')
        ax1.set_ylabel('Hit Ratio')
        ax1.set_title('Hit Ratio Comparison Across Patterns')
        ax1.set_xticks(x)
        ax1.set_xticklabels(patterns)
        ax1.set_ylim(0, 1)
        ax1.legend()
        
        self.hit_ratio_fig.tight_layout()
        self.hit_ratio_canvas.figure = self.hit_ratio_fig
        self.hit_ratio_canvas.draw()
        
        # Miss ratio figure
        self.miss_ratio_fig = Figure(figsize=(8, 5))
        ax2 = self.miss_ratio_fig.add_subplot(111)
        
        for i, config in enumerate(configs):
            miss_ratios = [1 - multi_results[p][i]["Hit Ratio"] for p in patterns]
            ax2.bar(x + i*width - 0.4 + width/2, miss_ratios, width, label=config)
        
        ax2.set_xlabel('Access Pattern')
        ax2.set_ylabel('Miss Ratio')
        ax2.set_title('Miss Ratio Comparison Across Patterns')
        ax2.set_xticks(x)
        ax2.set_xticklabels(patterns)
        ax2.set_ylim(0, 1)
        ax2.legend()
        
        self.miss_ratio_fig.tight_layout()
        self.miss_ratio_canvas.figure = self.miss_ratio_fig
        self.miss_ratio_canvas.draw()
        
        # Pattern performance figure
        self.pattern_perf_fig = Figure(figsize=(8, 5))
        ax3 = self.pattern_perf_fig.add_subplot(111)
        
        # Create a performance heatmap
        perf_data = np.zeros((len(patterns), len(configs)))
        for i, pattern in enumerate(patterns):
            for j, _ in enumerate(configs):
                perf_data[i, j] = multi_results[pattern][j]["Hit Ratio"]
        
        im = ax3.imshow(perf_data, cmap='RdYlGn', aspect='auto', vmin=0, vmax=1)
        
        # Add colorbar
        cbar = self.pattern_perf_fig.colorbar(im, ax=ax3)
        cbar.set_label('Hit Ratio')
        
        # Customize axes
        ax3.set_xticks(np.arange(len(configs)))
        ax3.set_yticks(np.arange(len(patterns)))
        ax3.set_xticklabels(configs)
        ax3.set_yticklabels(patterns)
        plt.setp(ax3.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")
        
        ax3.set_title('Pattern Performance Heatmap')
        
        # Add hit ratio values to cells
        for i in range(len(patterns)):
            for j in range(len(configs)):
                text = ax3.text(j, i, f'{perf_data[i, j]:.2f}',
                                ha="center", va="center", color="black")
        
        self.pattern_perf_fig.tight_layout()
        self.pattern_perf_canvas.figure = self.pattern_perf_fig
        self.pattern_perf_canvas.draw()

# Cell 5: Main

if __name__ == "__main__":
    app = CacheSimulatorApp()
    app.mainloop() 

# Cell 6: Memory Access Pattern Generators and Analyzers

def generate_memory_access_pattern(pattern_type, size, **kwargs):
    """
    Generate a memory access pattern
    
    Parameters:
    - pattern_type: Type of pattern ('sequential', 'random', 'loop', etc.)
    - size: Number of memory accesses
    - kwargs: Additional parameters specific to each pattern type
    
    Returns:
    - List of memory addresses
    """
    start_addr = kwargs.get('start_addr', 0)
    max_addr = kwargs.get('max_addr', 1000)
    seed = kwargs.get('seed', 42)
    np.random.seed(seed)
    
    if pattern_type == "sequential":
        # Sequential access with configurable stride
        stride = kwargs.get('stride', 4)
        return list(range(start_addr, start_addr + size * stride, stride))
    
    elif pattern_type == "random":
        # Random access with configurable distribution
        distribution = kwargs.get('distribution', 'uniform')
        if distribution == 'uniform':
            return list(np.random.randint(0, max_addr, size) * 4)
        elif distribution == 'gaussian':
            # Gaussian distribution centered at max_addr/2
            mean = max_addr / 2
            std_dev = max_addr / 6
            addresses = np.random.normal(mean, std_dev, size)
            return [int(max(0, min(addr, max_addr-1))) * 4 for addr in addresses]
    
    elif pattern_type == "loop":
        # Loop pattern with configurable loop size
        loop_size = kwargs.get('loop_size', min(size, 25))
        repeats = size // loop_size + (1 if size % loop_size > 0 else 0)
        pattern = []
        for _ in range(repeats):
            pattern.extend(range(start_addr, start_addr + loop_size * 4, 4))
        return pattern[:size]
    
    elif pattern_type == "stride":
        # Strided access pattern
        stride = kwargs.get('stride', 16)
        return list(range(start_addr, start_addr + size * stride, stride))
    
    elif pattern_type == "reverse":
        # Reverse sequential
        stride = kwargs.get('stride', 4)
        return list(range(start_addr + (size-1) * stride, start_addr - stride, -stride))
    
    elif pattern_type == "locality":
        # Temporal locality pattern
        hot_region_size = kwargs.get('hot_region_size', max_addr // 5)
        hot_access_prob = kwargs.get('hot_access_prob', 0.8)
        pattern = []
        
        for _ in range(size):
            if np.random.random() < hot_access_prob:  # Access to hot region
                addr = np.random.randint(0, hot_region_size)
            else:  # Access to rest of memory
                addr = np.random.randint(hot_region_size, max_addr)
            pattern.append(addr * 4)
        
        return pattern
    
    elif pattern_type == "mixed":
        # Mix of different patterns
        pattern_mix = kwargs.get('pattern_mix', [
            ('sequential', 0.3),
            ('random', 0.3),
            ('loop', 0.4)
        ])
        
        pattern = []
        remaining = size
        
        for p_type, p_ratio in pattern_mix:
            p_size = int(size * p_ratio)
            if p_type == pattern_mix[-1][0]:  # Last pattern takes all remaining
                p_size = remaining
            
            if p_type == 'sequential':
                sub_pattern = list(range(start_addr, start_addr + p_size * 4, 4))
            elif p_type == 'random':
                sub_pattern = list(np.random.randint(0, max_addr, p_size) * 4)
            elif p_type == 'loop':
                loop_size = min(p_size, 25)
                repeats = p_size // loop_size + (1 if p_size % loop_size > 0 else 0)
                sub_pattern = []
                for _ in range(repeats):
                    sub_pattern.extend(range(start_addr, start_addr + loop_size * 4, 4))
                sub_pattern = sub_pattern[:p_size]
            
            pattern.extend(sub_pattern)
            remaining -= p_size
        
        return pattern
    
    elif pattern_type == "realistic":
        # Realistic workload simulation
        # 60% locality around a few hot spots, 30% sequential, 10% random
        hot_spots = kwargs.get('hot_spots', 3)
        hot_regions = []
        
        # Define hot regions
        for _ in range(hot_spots):
            region_start = np.random.randint(0, max_addr - 100)
            region_size = np.random.randint(20, 100)
            hot_regions.append((region_start, region_size))
        
        pattern = []
        for _ in range(size):
            r = np.random.random()
            if r < 0.6:  # Access to a hot region (60%)
                region = hot_regions[np.random.randint(0, len(hot_regions))]
                addr = np.random.randint(region[0], region[0] + region[1])
                pattern.append(addr * 4)
            elif r < 0.9:  # Sequential access (30%)
                seq_start = start_addr + len(pattern)
                pattern.append(seq_start * 4)
            else:  # Random access (10%)
                addr = np.random.randint(0, max_addr)
                pattern.append(addr * 4)
        
        return pattern
    
    else:
        raise ValueError(f"Unknown pattern type: {pattern_type}")

def analyze_access_pattern(addresses):
    """
    Analyze a memory access pattern
    
    Parameters:
    - addresses: List of memory addresses
    
    Returns:
    - Dictionary with analysis results
    """
    if not addresses:
        return {}
    
    # Calculate basic statistics
    unique_addresses = len(set(addresses))
    address_counts = {}
    for addr in addresses:
        address_counts[addr] = address_counts.get(addr, 0) + 1
    
    # Identify hot addresses (accessed more than average)
    avg_access_count = len(addresses) / unique_addresses
    hot_addresses = {addr: count for addr, count in address_counts.items() 
                    if count > avg_access_count * 1.5}
    
    # Calculate sequential access percentage
    sequential_count = 0
    for i in range(1, len(addresses)):
        if addresses[i] - addresses[i-1] == 4:
            sequential_count += 1
    sequential_percentage = sequential_count / (len(addresses) - 1) if len(addresses) > 1 else 0
    
    # Calculate spatial locality
    spatial_locality = 0
    for i in range(1, len(addresses)):
        # If addresses are within 100 bytes of each other
        if abs(addresses[i] - addresses[i-1]) <= 100:
            spatial_locality += 1
    spatial_locality = spatial_locality / (len(addresses) - 1) if len(addresses) > 1 else 0
    
    # Calculate temporal locality
    reuse_distances = []
    addr_last_seen = {}
    for i, addr in enumerate(addresses):
        if addr in addr_last_seen:
            reuse_distances.append(i - addr_last_seen[addr])
        addr_last_seen[addr] = i
    
    avg_reuse_distance = sum(reuse_distances) / len(reuse_distances) if reuse_distances else 0
    temporal_locality = 1 / (1 + avg_reuse_distance) if avg_reuse_distance > 0 else 0
    
    return {
        "total_accesses": len(addresses),
        "unique_addresses": unique_addresses,
        "address_diversity": unique_addresses / len(addresses),
        "hot_addresses": len(hot_addresses),
        "sequential_percentage": sequential_percentage,
        "spatial_locality": spatial_locality,
        "temporal_locality": temporal_locality,
        "avg_reuse_distance": avg_reuse_distance
    }

def predict_cache_performance(pattern_analysis, cache_config):
    """
    Predict cache performance based on pattern analysis and cache configuration
    
    Parameters:
    - pattern_analysis: Output from analyze_access_pattern
    - cache_config: Dictionary with cache configuration
    
    Returns:
    - Dictionary with performance predictions
    """
    cache_size = cache_config.get("cache_size", 256)
    block_size = cache_config.get("block_size", 16)
    associativity = cache_config.get("associativity", 1)
    policy = cache_config.get("policy", "LRU")
    
    # Calculate number of blocks in cache
    num_blocks = cache_size // block_size
    
    # Theoretical maximum number of unique blocks that can be stored
    max_blocks = num_blocks
    
    # Adjust for associativity
    if associativity > 1:
        num_sets = num_blocks // associativity
    else:
        num_sets = num_blocks  # Direct mapped
    
    # Predict hit ratio based on pattern analysis
    address_diversity = pattern_analysis["address_diversity"]
    spatial_locality = pattern_analysis["spatial_locality"]
    temporal_locality = pattern_analysis["temporal_locality"]
    sequential_percentage = pattern_analysis["sequential_percentage"]
    
    # Base prediction on the working set size vs. cache size
    # and locality characteristics
    working_set_ratio = pattern_analysis["unique_addresses"] / max_blocks
    
    if working_set_ratio <= 1:
        # Working set fits in cache
        base_hit_ratio = 0.9 - (working_set_ratio * 0.2)
    else:
        # Working set larger than cache
        base_hit_ratio = 0.7 * (1 / working_set_ratio)
    
    # Adjust for spatial locality
    spatial_bonus = spatial_locality * 0.2
    
    # Adjust for temporal locality
    temporal_bonus = temporal_locality * 0.3
    
    # Adjust for sequential access (good for prefetching)
    sequential_bonus = sequential_percentage * 0.1
    
    # Adjust for associativity
    if associativity == 1:  # Direct mapped
        associativity_factor = 1.0
    elif associativity < 4:  # Low associativity
        associativity_factor = 1.1
    else:  # High associativity
        associativity_factor = 1.2
    
    # Adjust for replacement policy
    policy_factor = 1.1 if policy == "LRU" else 1.0
    
    # Calculate predicted hit ratio
    predicted_hit_ratio = min(0.99, max(0.01, 
        (base_hit_ratio + spatial_bonus + temporal_bonus + sequential_bonus) * 
        associativity_factor * policy_factor))
    
    # Confidence of prediction (higher is better)
    confidence = 0.7 - (0.1 * working_set_ratio if working_set_ratio > 1 else 0)
    
    return {
        "predicted_hit_ratio": predicted_hit_ratio,
        "predicted_miss_ratio": 1 - predicted_hit_ratio,
        "confidence": confidence,
        "working_set_ratio": working_set_ratio,
        "cache_utilization": min(1.0, 1 / working_set_ratio),
        "spatial_locality_score": spatial_locality,
        "temporal_locality_score": temporal_locality,
        "sequential_access_score": sequential_percentage
    } 