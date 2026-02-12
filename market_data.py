import requests
import pandas as pd
from datetime import datetime, timedelta

class BondowosoMarketData:
    def __init__(self):
        self.url = "https://api-sp2kp.kemendag.go.id/report/api/average-price/export-area-daily-json"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0",
        }
        # Default payload for Bondowoso (Pasar Induk)
        self.default_payload = {
            'level': (None, '3'),
            'kode_provinsi': (None, '35'),
            'kode_kab_kota': (None, '3511'), # Bondowoso
            'pasar_id': (None, '406'),        # Pasar Induk
            'skip_sat_sun': (None, 'true'),
            'tipe_komoditas': (None, '1'),
            # The full list of commodity IDs - STORED AS DEFAULT FOR "ALL"
            'variant_ids': (None, '37,13,38,39,29,52,51,9,2,11,10,6,43,27,49,50,22,53,19,21,41,14,15,24,30,23,20,34,55,46,4,45,48,58,28,8,57,47,12,3,42,16,17,18,7,54,5,32,33,31,35,44,25,36,26,56,40')
        }
        self.all_variant_ids = self.default_payload['variant_ids'][1] # Store original "All" string
        self._cached_df = None

    def select_variants(self, variants):
        """
        Modifies the payload to fetch specific variants.
        
        Args:
            variants (list or str): 
                - If "All" (case-insensitive string), resets to fetch all default IDs.
                - If list of IDs (e.g. [13, 38, '52']), updates payload to fetch only those.
        """
        if isinstance(variants, str) and variants.lower() == "all":
            # Reset to original full list
            self.default_payload['variant_ids'] = (None, self.all_variant_ids)
            print("✅ Variant selection reset to ALL.")
        
        elif isinstance(variants, list):
            ids_str = ",".join(str(v) for v in variants)
            self.default_payload['variant_ids'] = (None, ids_str)
            print(f"✅ Variant selection updated to: {ids_str}")
            
        else:
            print("⚠️ Invalid input for select_variants. Use a list of IDs or 'All'.")

    def fetch_raw_data(self, start_date_str, end_date_str):
        print(f"📡 Fetching from API ({start_date_str} to {end_date_str})...")
        
        payload = self.default_payload.copy()
        payload['start_date'] = (None, start_date_str)
        payload['end_date'] = (None, end_date_str)

        try:
            response = requests.post(self.url, files=payload, headers=self.headers, timeout=20)
            
            if response.status_code == 200:
                json_data = response.json()
                if json_data.get("status") == "success":
                    return json_data.get("data", [])
                else:
                    print(f"⚠️ API Error: {json_data.get('message')}")
            else:
                print(f"❌ HTTP Error: {response.status_code}")
        except Exception as e:
            print(f"❌ Connection Error: {e}")
        
        return None
    def process_to_dataframe(self, raw_items):
        if not raw_items:
            return pd.DataFrame()

        rows = []
        for item in raw_items:
            # Base info
            row = {
                "Var ID": item.get("variant_id"),
                "Variant Name": item.get("variant"),
            }
            for price_entry in item.get("daftarHarga", []):
                date_key = price_entry.get("date")
                row[date_key] = int(price_entry.get("harga", 0))
            
            rows.append(row)

        df = pd.DataFrame(rows)
        fixed_cols = ["Var ID", "Variant Name"]
        date_cols = [c for c in df.columns if c not in fixed_cols]
        date_cols.sort()
        
        final_cols = fixed_cols + date_cols
        self._cached_df = df[final_cols] # Cache it
        return self._cached_df

    def save_to_csv(self, df, filename="bondowoso_prices.csv"):
        try:
            if df is not None and not df.empty:
                df.to_csv(filename, index=False)
                print(f"💾 Saved CSV to: {filename}")
                return True
            print("⚠️ No data to save.")
            return False
        except Exception as e:
            print(f"❌ Save Error: {e}")
            return False

    def get_data(self, days=4, save_csv=False, filename="bondowoso_prices.csv"):
        """
        One-stop function for external modules.
        - Calculates dates automatically.
        - Fetches, processes, and optionally saves.
        - Returns the DataFrame directly.
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        s_str = start_date.strftime("%Y-%m-%d")
        e_str = end_date.strftime("%Y-%m-%d")
        raw = self.fetch_raw_data(s_str, e_str)
        df = self.process_to_dataframe(raw)
        if save_csv:
            self.save_to_csv(df, filename)
        return df

if __name__ == "__main__":
    market = BondowosoMarketData()
    
    # Test 1: Select Specific Items (e.g., Beras Medium (52) & Cabe Merah (9))
    market.select_variants([52, 9]) 
    df_specific = market.get_data(days=100)
    print("\n--- Specific Data ---")
    print(df_specific)
    market.save_to_csv(df_specific, "100_days.csv")

    market.select_variants("All")
    df_all = market.get_data(days=2)
    print("\n--- All Data (Head) ---")
    print(df_all.head())