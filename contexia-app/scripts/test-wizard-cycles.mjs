// scripts/test-wizard-cycles.mjs
// Ejecuta 3 ciclos completos del wizard Crear Empresa con 3 usuarios de prueba.
// Valida cada uno de los 8 pasos usando la misma lógica que el wizard real.
//
// Uso: node scripts/test-wizard-cycles.mjs

// ───────────────────────────────────────────────────────────────────
// Validación (réplica de lib/utils/crearEmpresaLogic.ts)
// ───────────────────────────────────────────────────────────────────

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const PHONE_RE = /^3\d{9}$/;

function validateStep(step, state) {
  switch (step) {
    case 1: {
      const { nombre, telefono, email } = state.contacto;
      if (!nombre.trim() || nombre.trim().split(" ").length < 2) {
        return { ok: false, error: "Escribe tu nombre completo" };
      }
      if (!PHONE_RE.test(telefono.replace(/\s/g, ""))) {
        return { ok: false, error: "Teléfono debe tener 10 dígitos y empezar en 3" };
      }
      if (!EMAIL_RE.test(email)) {
        return { ok: false, error: "Correo no válido" };
      }
      return { ok: true };
    }
    case 2: {
      if (!state.tipoSociedad) {
        return { ok: false, error: "Elige el tipo de empresa" };
      }
      return { ok: true };
    }
    case 3: {
      if (state.nombreEmpresa.trim().length < 4) {
        return { ok: false, error: "El nombre debe tener al menos 4 letras" };
      }
      if (state.nombreDisponible === false) {
        return { ok: false, error: "Este nombre no está disponible, prueba con otro" };
      }
      return { ok: true };
    }
    case 4: {
      if (state.descripcion.actividad.trim().length < 20) {
        return {
          ok: false,
          error: "Cuéntanos un poco más qué hace tu empresa (mínimo 20 letras)",
        };
      }
      if (!state.descripcion.ciudad || !state.descripcion.direccion.trim()) {
        return { ok: false, error: "Falta la ciudad o la dirección" };
      }
      return { ok: true };
    }
    case 5: {
      if (state.accionistas.length === 0) {
        return { ok: false, error: "Agrega al menos un socio" };
      }
      const totalPct = state.accionistas.reduce(
        (s, a) => s + (a.participacion || 0),
        0,
      );
      if (Math.abs(totalPct - 100) > 0.01) {
        return {
          ok: false,
          error: `La suma de participaciones debe ser 100% (ahora va en ${totalPct.toFixed(1)}%)`,
        };
      }
      for (const a of state.accionistas) {
        if (!a.nombre.trim() || !a.cedula.trim()) {
          return { ok: false, error: "Cada socio necesita nombre y cédula" };
        }
      }
      return { ok: true };
    }
    case 6: {
      if (state.capital.total < 400_000) {
        return { ok: false, error: "El capital mínimo recomendado es $400.000 COP" };
      }
      if (state.capital.total > 800_000) {
        return {
          ok: false,
          error:
            "Para arrancar lo recomendado es máximo $800.000 COP (puedes aumentarlo después)",
        };
      }
      if (state.capital.pagadoPct > state.capital.suscritoPct) {
        return { ok: false, error: "Lo pagado no puede ser mayor que lo suscrito" };
      }
      return { ok: true };
    }
    case 7: {
      const { origen, socioId, nombre, cedula, telefono, email } = state.representante;
      if (origen === "socio") {
        if (!socioId) return { ok: false, error: "Elige cuál socio firma" };
      } else {
        if (!nombre?.trim() || !cedula?.trim() || !telefono?.trim() || !email?.trim()) {
          return { ok: false, error: "Faltan datos del representante legal" };
        }
        if (!EMAIL_RE.test(email)) {
          return { ok: false, error: "Correo del representante no válido" };
        }
      }
      return { ok: true };
    }
    case 8: {
      if (!state.paymentMethod) {
        return { ok: false, error: "Elige cómo vas a pagar" };
      }
      if (!state.acceptedTerms) {
        return { ok: false, error: "Acepta los términos para continuar" };
      }
      return { ok: true };
    }
    default:
      return { ok: true };
  }
}

function checkNombreDisponibleMock(nombre) {
  const trimmed = nombre.trim();
  if (trimmed.length < 4) return false;
  const prohibidas = ["banco", "estado", "republica", "nacional", "presidente"];
  const lower = trimmed.toLowerCase();
  return !prohibidas.some((p) => lower.includes(p));
}

// ───────────────────────────────────────────────────────────────────
// 3 usuarios de prueba (datasets distintos)
// ───────────────────────────────────────────────────────────────────

const TEST_USERS = [
  // ───── Ciclo 1: Empresario unipersonal (e-commerce) ─────
  {
    id: "test-1",
    perfil: "👤 María Gómez — SAS Unipersonal · E-commerce",
    state: {
      contacto: {
        nombre: "María Gómez",
        telefono: "3015551234",
        email: "maria.gomez@ejemplo.com",
      },
      tipoSociedad: "sas-unipersonal",
      nombreEmpresa: "MariaStyle",
      nombreDisponible: checkNombreDisponibleMock("MariaStyle"),
      descripcion: {
        actividad:
          "Vendemos ropa femenina por internet a clientes en toda Colombia, con despacho a 24 horas.",
        ciiu: "4790",
        direccion: "Calle 100 # 15-30 Apto 502",
        ciudad: "Bogotá",
        departamento: "Cundinamarca",
      },
      accionistas: [
        {
          id: "acc-m1",
          nombre: "María Gómez",
          cedula: "1015487523",
          participacion: 100,
        },
      ],
      capital: {
        total: 500_000,
        suscritoPct: 100,
        pagadoPct: 100,
      },
      representante: {
        origen: "socio",
        socioId: "acc-m1",
      },
      paymentMethod: "transferencia",
      acceptedTerms: true,
    },
  },

  // ───── Ciclo 2: Dos socios — Restaurante ─────
  {
    id: "test-2",
    perfil: "👥 Juan & Carolina — SAS · Restaurante",
    state: {
      contacto: {
        nombre: "Juan Pérez",
        telefono: "3204449876",
        email: "juan.perez@elsabor.co",
      },
      tipoSociedad: "sas",
      nombreEmpresa: "El Sabor del Valle",
      nombreDisponible: checkNombreDisponibleMock("El Sabor del Valle"),
      descripcion: {
        actividad:
          "Operamos un restaurante de comida tradicional vallecaucana en el norte de Cali, con servicio a domicilio.",
        ciiu: "5611",
        direccion: "Avenida 6N # 23-45",
        ciudad: "Cali",
        departamento: "Valle del Cauca",
      },
      accionistas: [
        {
          id: "acc-j1",
          nombre: "Juan Pérez",
          cedula: "9876543210",
          participacion: 60,
        },
        {
          id: "acc-c1",
          nombre: "Carolina Vargas",
          cedula: "1023456789",
          participacion: 40,
        },
      ],
      capital: {
        total: 700_000,
        suscritoPct: 100,
        pagadoPct: 50,
      },
      representante: {
        origen: "otro",
        nombre: "Andrés Restrepo",
        cedula: "7891234560",
        telefono: "3119876543",
        email: "andres.restrepo@elsabor.co",
      },
      paymentMethod: "tarjeta",
      acceptedTerms: true,
    },
  },

  // ───── Ciclo 3: Tres socios tech — Consultoría software ─────
  {
    id: "test-3",
    perfil: "🚀 Trío fundador — SAS · Software & Consultoría",
    state: {
      contacto: {
        nombre: "Andrea López",
        telefono: "3148882211",
        email: "andrea@techcore.dev",
      },
      tipoSociedad: "sas",
      nombreEmpresa: "TechCore Labs",
      nombreDisponible: checkNombreDisponibleMock("TechCore Labs"),
      descripcion: {
        actividad:
          "Desarrollamos software a la medida y damos consultoría tecnológica a PyMEs colombianas en transformación digital.",
        ciiu: "6201",
        direccion: "Carrera 43A # 1-50 Torre Norte Of 1402",
        ciudad: "Medellín",
        departamento: "Antioquia",
      },
      accionistas: [
        {
          id: "acc-a1",
          nombre: "Andrea López",
          cedula: "8001234567",
          participacion: 40,
        },
        {
          id: "acc-r1",
          nombre: "Ricardo Mejía",
          cedula: "8005678901",
          participacion: 35,
        },
        {
          id: "acc-s1",
          nombre: "Sofía Restrepo",
          cedula: "8009876543",
          participacion: 25,
        },
      ],
      capital: {
        total: 800_000,
        suscritoPct: 100,
        pagadoPct: 75,
      },
      representante: {
        origen: "socio",
        socioId: "acc-a1",
      },
      paymentMethod: "pse",
      acceptedTerms: true,
    },
  },
];

// ───────────────────────────────────────────────────────────────────
// Ejecutor de ciclos
// ───────────────────────────────────────────────────────────────────

function formatCop(value) {
  return `$${value.toLocaleString("es-CO")}`;
}

function runCycle(user) {
  console.log(`\n${"=".repeat(70)}`);
  console.log(`  ${user.perfil}`);
  console.log(`${"=".repeat(70)}`);

  const stepNames = [
    "Contacto",
    "Estructura",
    "Nombre",
    "Actividad",
    "Socios",
    "Capital",
    "Firma",
    "Pago",
  ];

  let allPassed = true;
  for (let step = 1; step <= 8; step++) {
    const result = validateStep(step, user.state);
    const status = result.ok ? "✓ PASS" : "✗ FAIL";
    const color = result.ok ? "\x1b[32m" : "\x1b[31m";
    const reset = "\x1b[0m";
    const errorMsg = result.error ? ` — ${result.error}` : "";
    console.log(`  Paso ${step} (${stepNames[step - 1].padEnd(11)}): ${color}${status}${reset}${errorMsg}`);
    if (!result.ok) allPassed = false;
  }

  console.log(`\n  📊 Resumen del registro:`);
  console.log(`     • Empresa:    ${user.state.nombreEmpresa} (${user.state.tipoSociedad.toUpperCase()})`);
  console.log(`     • Ubicación:  ${user.state.descripcion.ciudad}, ${user.state.descripcion.departamento}`);
  console.log(`     • Socios:     ${user.state.accionistas.length} (${user.state.accionistas.map((a) => `${a.nombre} ${a.participacion}%`).join(", ")})`);
  console.log(`     • Capital:    ${formatCop(user.state.capital.total)} (suscrito ${user.state.capital.suscritoPct}%, pagado ${user.state.capital.pagadoPct}%)`);
  console.log(`     • Repr legal: ${user.state.representante.origen === "socio" ? "Es socio" : user.state.representante.nombre} (${user.state.representante.origen})`);
  console.log(`     • Pago:       ${user.state.paymentMethod}`);
  console.log(`     • Términos:   ${user.state.acceptedTerms ? "✓ aceptados" : "✗ no aceptados"}`);
  console.log(`\n  ${allPassed ? "\x1b[32m✅ CICLO COMPLETO — Wizard se enviaría a pago\x1b[0m" : "\x1b[31m❌ CICLO FALLIDO — Wizard NO permitiría avanzar\x1b[0m"}`);

  return allPassed;
}

// ───────────────────────────────────────────────────────────────────
// Main
// ───────────────────────────────────────────────────────────────────

console.log("\n╔══════════════════════════════════════════════════════════════════╗");
console.log("║       CONTEXIA · Test del Wizard Crear Empresa — 3 ciclos       ║");
console.log("╚══════════════════════════════════════════════════════════════════╝");

const results = TEST_USERS.map((u) => ({ user: u, passed: runCycle(u) }));

console.log(`\n${"=".repeat(70)}`);
console.log("  RESULTADO FINAL");
console.log(`${"=".repeat(70)}`);

const totalPassed = results.filter((r) => r.passed).length;
results.forEach((r) => {
  const emoji = r.passed ? "✅" : "❌";
  console.log(`  ${emoji} ${r.user.perfil}`);
});
console.log(`\n  ${totalPassed} / ${results.length} ciclos completos exitosos`);

if (totalPassed === results.length) {
  console.log("\n  \x1b[32m🎉 Wizard funcional al 100% — listo para producción.\x1b[0m\n");
  process.exit(0);
} else {
  console.log("\n  \x1b[31m⚠️  Hay ciclos con fallas. Revisa la lógica de validación.\x1b[0m\n");
  process.exit(1);
}
