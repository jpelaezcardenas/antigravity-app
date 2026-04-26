from typing import List
from datetime import date
from infrastructure.supabase_client import supabase
from domain.transaccion import Transaccion, TransaccionCreate

class TransaccionRepository:
    def get_by_user(self, user_id: str, limit: int = 50) -> List[Transaccion]:
        response = supabase.table("transactions")\
            .select("*")\
            .eq("usuario_id", user_id)\
            .order("fecha", desc=True)\
            .limit(limit)\
            .execute()
        return [Transaccion(**item) for item in response.data]

    def get_by_date_range(self, user_id: str, start_date: date, end_date: date) -> List[Transaccion]:
        response = supabase.table("transactions")\
            .select("*")\
            .eq("usuario_id", user_id)\
            .gte("fecha", start_date.isoformat())\
            .lte("fecha", end_date.isoformat())\
            .execute()
        return [Transaccion(**item) for item in response.data]

    def create(self, trans: TransaccionCreate) -> Transaccion:
        data = trans.model_dump()
        data["fecha"] = data["fecha"].isoformat()
        response = supabase.table("transactions").insert(data).execute()
        return Transaccion(**response.data[0])

    def bulk_create(self, trans_list: List[TransaccionCreate]) -> List[Transaccion]:
        data = [t.model_dump() for t in trans_list]
        for item in data:
            item["fecha"] = item["fecha"].isoformat()
        response = supabase.table("transactions").insert(data).execute()
        return [Transaccion(**item) for item in response.data]
