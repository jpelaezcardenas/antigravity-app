import { NextRequest, NextResponse } from "next/server";
import { supabaseAdmin } from "@/lib/supabase";

export async function POST(req: NextRequest) {
  try {
    // Disable RLS on leads table
    const { data, error } = await supabaseAdmin
      .rpc("__exec_sql", {
        sql: "ALTER TABLE leads DISABLE ROW LEVEL SECURITY;",
      } as any)
      .catch(() => null);

    if (error) {
      // Try direct SQL query if RPC doesn't work
      const result = await supabaseAdmin.from("_test").select().then(
        () => ({ success: true }),
        (e) => ({ error: String(e) })
      );

      // Actually, we need to use a different approach
      // Let's just return the SQL command to run manually
      return NextResponse.json({
        status: "manual",
        message: "RLS cannot be disabled via SDK. Run this in Supabase SQL Editor:",
        sql: "ALTER TABLE leads DISABLE ROW LEVEL SECURITY;",
      });
    }

    return NextResponse.json({
      status: "success",
      message: "RLS on leads table has been disabled",
    });
  } catch (err) {
    return NextResponse.json(
      { error: String(err) },
      { status: 500 }
    );
  }
}
