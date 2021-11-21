use duct::cmd;
use std::array::IntoIter;
use std::collections::HashMap;
use std::io::prelude::*;
use std::{
    io::{BufRead, BufReader},
    process::{Command, Stdio},
};

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
        (180, "🎧", "play an MP3 song"),
        (448, "🪅", "destroy a piñata"),
        (5_100, "💡", "power an LED for 10 minutes"),
        (29_000, "📱", "charge a phone"),
        (67_500, "🍞", "toast a toast"),
        (82_500, "🫖", "brew a cup of coffee"),
        (108_000, "📺", "run a TV for 1 hour"),
        (110_000, "🎢", "ride a roller coaster"),
        (143_000, "📧", "send an email"),
        (180_000, "💻", "run a laptop for 1 hour"),
        (360_000, "🎮", "play video games for 1 hour"),
        (564_000, "🫖", "brew a cup of tea"),
        (1_250_000, "🧱", "break through a brick"),
        (3_400_000, "🍕", "bake a pizza"),
        (5_400_000, "🎂", "bake a cake"),
        (10_800_000, "🍪", "bake cookies"),
        (248_000_000, "🏠", "power an average house for 1 day"),
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
    // 14_000_000_000_000_000_000_000_000_000_000: ☀️ Run the sun for 1 hour

    // let perf_output = Command::new("sudo")
    //     .args([
    //         "perf",
    //         "stat",
    //         "-I",
    //         "1000",
    //         "-e",
    //         "power/energy-pkg/",
    //         "-a",
    //     ])
    //     .stdout(Stdio::piped())
    //     .spawn()
    //     .unwrap()
    //     .stdout
    //     .unwrap();
    // let perf_output = BufReader::new(perf_output);
    // perf_output.lines().for_each(|line| {
    //     println!("Read a line!");
    //     println!("Read: {:?}", line.unwrap());
    // });

    // {
    //     let stdout = perf.stdout.as_mut().unwrap();
    //     let stdout_reader = BufReader::new(stdout);
    //     let stdout_lines = stdout_reader.lines();

    //     println!("Reading stdout lines");
    //     for line in stdout_lines {
    //         println!("Read a line!");
    //         println!("Read: {:?}", line);
    //     }
    // }

    // println!("Waiting for perf");
    // perf.wait().unwrap();

    // let perf = Command::new("sudo")
    //     .args([
    //         "perf",
    //         "stat",
    //         "-I",
    //         "1000",
    //         "-e",
    //         "power/energy-pkg/",
    //         "-a",
    //     ])
    //     .spawn()
    //     .unwrap();
    // let stdout = BufReader::new(perf.stdout.unwrap());
    // for line in stdout.lines() {
    //     println!("{}", line.unwrap());
    // }

    Ok(())
}
