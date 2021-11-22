use duct::cmd;
use std::io::{BufRead, BufReader};

fn main() -> std::io::Result<()> {
    let big_cmd = cmd!(
        "sudo",
        "perf",
        "stat",
        "-I",
        "1000",
        "-e",
        "power/energy-pkg/",
        "-a"
    );
    let reader = big_cmd.stderr_to_stdout().reader()?;
    let joules_stream = BufReader::new(reader)
        .lines()
        .flatten()
        .filter(|line| !line.starts_with('#'))
        .map(|line| {
            let mut parts = line.split_ascii_whitespace();
            let _time = parts.next().unwrap();
            let counts = parts.next().unwrap();
            assert_eq!(parts.next(), Some("Joules"));
            assert_eq!(parts.next(), Some("power/energy-pkg/"));
            let joules: f64 = counts.replace(',', ".").parse().unwrap();
            joules
        });

    let comparisons = [
        (180.0, "🎧", "play an MP3 song"),
        (448.0, "🪅", "crack a piñata"),
        (5_100.0, "💡", "power an LED for 10 minutes"),
        (29_000.0, "📱", "charge a phone"),
        (67_500.0, "🍞", "toast a toast"),
        (82_500.0, "🫖", "brew a cup of coffee"),
        (108_000.0, "📺", "run a TV for 1 hour"),
        (110_000.0, "🎢", "ride a roller coaster"),
        (143_000.0, "📧", "send an email"),
        (180_000.0, "💻", "run a laptop for 1 hour"),
        (360_000.0, "🎮", "play video games for 1 hour"),
        (564_000.0, "🫖", "brew a cup of tea"),
        (1_250_000.0, "🧱", "break through a brick"),
        (3_400_000.0, "🍕", "bake a pizza"),
        (5_400_000.0, "🎂", "bake a cake"),
        (10_800_000.0, "🍪", "bake cookies"),
        (248_000_000.0, "🏠", "power an average house for 1 day"),
        (
            14_000_000_000_000_000_000_000_000_000_000.0,
            "🌅",
            "Run the sun for 1 hour",
        ),
        // Emojis for other things that might be interesting:
        // 💣 Bomb
        // 💎 Gem Stone
        // 📻 Radio
        // 🔦 Flashlight
        // 🗽 Statue of Liberty
        // 🚂 Locomotive
        // ✈️️ Airplane
        // 🚢 Ship
        // 🚁 Helicopter
        // 🚀 Rocket
        // 🏊 Person Swimming
        // 🏋️ Person Lifting Weights
        // 🚴 Person Biking
    ];
    let mut total_joules = 0.0;
    for joules in joules_stream {
        total_joules += joules;
        let comparison = comparisons
            .iter()
            .rev()
            .filter(|it| total_joules >= it.0 as f64)
            .nth(0)
            .map(|it| (it.1, it.2));
        print!(
            "Current energy use: {:.2} joules. Since program start: {:.1} joules.",
            joules, total_joules
        );
        if let Some((emoji, text)) = comparison {
            print!(" With this energy, you could {}. {}", text, emoji);
        }
        println!();
    }

    Ok(())
}
