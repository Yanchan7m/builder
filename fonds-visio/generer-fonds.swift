import Foundation
import CoreGraphics
import CoreImage
import ImageIO

let W = 1920, H = 1080

struct Blob { let x: Double; let y: Double; let r: Double; let c: (Double, Double, Double) }
struct Palette { let name: String; let base: (Double, Double, Double); let blobs: [Blob] }

func rgb(_ r: Int, _ g: Int, _ b: Int) -> (Double, Double, Double) {
    (Double(r) / 255.0, Double(g) / 255.0, Double(b) / 255.0)
}

// Positions en fraction de l'image (0-1), rayon en fraction de la largeur.
let palettes: [Palette] = [
    Palette(name: "01-bleu-nuit", base: rgb(13, 20, 38), blobs: [
        Blob(x: 0.20, y: 0.25, r: 0.55, c: rgb(38, 62, 120)),
        Blob(x: 0.78, y: 0.70, r: 0.50, c: rgb(24, 90, 130)),
        Blob(x: 0.55, y: 0.10, r: 0.35, c: rgb(70, 50, 140)),
    ]),
    Palette(name: "02-violet-profond", base: rgb(22, 14, 34), blobs: [
        Blob(x: 0.25, y: 0.70, r: 0.55, c: rgb(86, 40, 120)),
        Blob(x: 0.80, y: 0.25, r: 0.48, c: rgb(120, 48, 108)),
        Blob(x: 0.50, y: 0.95, r: 0.35, c: rgb(48, 34, 96)),
    ]),
    Palette(name: "03-vert-foret", base: rgb(12, 26, 22), blobs: [
        Blob(x: 0.22, y: 0.30, r: 0.52, c: rgb(30, 72, 56)),
        Blob(x: 0.82, y: 0.72, r: 0.50, c: rgb(46, 92, 62)),
        Blob(x: 0.60, y: 0.05, r: 0.32, c: rgb(22, 60, 70)),
    ]),
    Palette(name: "04-graphite", base: rgb(26, 27, 30), blobs: [
        Blob(x: 0.30, y: 0.25, r: 0.55, c: rgb(58, 60, 66)),
        Blob(x: 0.75, y: 0.75, r: 0.50, c: rgb(42, 44, 50)),
        Blob(x: 0.90, y: 0.15, r: 0.30, c: rgb(72, 74, 82)),
    ]),
    Palette(name: "05-sarcelle", base: rgb(10, 30, 36), blobs: [
        Blob(x: 0.20, y: 0.72, r: 0.55, c: rgb(20, 78, 88)),
        Blob(x: 0.80, y: 0.28, r: 0.50, c: rgb(28, 100, 100)),
        Blob(x: 0.45, y: 0.50, r: 0.30, c: rgb(16, 56, 76)),
    ]),
    Palette(name: "06-bordeaux", base: rgb(30, 14, 18), blobs: [
        Blob(x: 0.25, y: 0.30, r: 0.52, c: rgb(96, 32, 44)),
        Blob(x: 0.78, y: 0.70, r: 0.50, c: rgb(120, 54, 44)),
        Blob(x: 0.55, y: 0.02, r: 0.32, c: rgb(64, 24, 48)),
    ]),
    Palette(name: "07-sable-chaud", base: rgb(42, 34, 28), blobs: [
        Blob(x: 0.28, y: 0.68, r: 0.55, c: rgb(112, 88, 62)),
        Blob(x: 0.80, y: 0.26, r: 0.48, c: rgb(134, 106, 72)),
        Blob(x: 0.50, y: 0.95, r: 0.32, c: rgb(80, 60, 46)),
    ]),
    Palette(name: "08-emeraude-minuit", base: rgb(8, 18, 26), blobs: [
        Blob(x: 0.75, y: 0.30, r: 0.55, c: rgb(18, 78, 74)),
        Blob(x: 0.22, y: 0.75, r: 0.48, c: rgb(24, 52, 88)),
        Blob(x: 0.50, y: 0.10, r: 0.30, c: rgb(14, 60, 60)),
    ]),
    Palette(name: "09-rose-lilas", base: rgb(34, 22, 34), blobs: [
        Blob(x: 0.24, y: 0.28, r: 0.54, c: rgb(122, 66, 106)),
        Blob(x: 0.80, y: 0.72, r: 0.50, c: rgb(92, 70, 134)),
        Blob(x: 0.55, y: 0.98, r: 0.32, c: rgb(140, 84, 96)),
    ]),
    Palette(name: "10-bleu-acier", base: rgb(20, 28, 40), blobs: [
        Blob(x: 0.78, y: 0.72, r: 0.55, c: rgb(52, 74, 104)),
        Blob(x: 0.22, y: 0.26, r: 0.50, c: rgb(40, 58, 88)),
        Blob(x: 0.60, y: 0.45, r: 0.30, c: rgb(66, 92, 122)),
    ]),
]

let space = CGColorSpaceCreateDeviceRGB()
let ciContext = CIContext(options: [.workingColorSpace: space])

let outDir = ("~/Pictures/Fonds visio" as NSString).expandingTildeInPath
try? FileManager.default.createDirectory(atPath: outDir, withIntermediateDirectories: true)

for p in palettes {
    guard let ctx = CGContext(data: nil, width: W, height: H, bitsPerComponent: 8,
                              bytesPerRow: 0, space: space,
                              bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue) else {
        FileHandle.standardError.write("contexte impossible pour \(p.name)\n".data(using: .utf8)!)
        continue
    }

    ctx.setFillColor(red: p.base.0, green: p.base.1, blue: p.base.2, alpha: 1)
    ctx.fill(CGRect(x: 0, y: 0, width: W, height: H))

    // Chaque tache = dégradé radial couleur -> transparent, empilé sur le fond.
    for b in p.blobs {
        let comps: [CGFloat] = [
            CGFloat(b.c.0), CGFloat(b.c.1), CGFloat(b.c.2), 0.95,
            CGFloat(b.c.0), CGFloat(b.c.1), CGFloat(b.c.2), 0.0,
        ]
        guard let grad = CGGradient(colorSpace: space, colorComponents: comps,
                                    locations: [0.0, 1.0], count: 2) else { continue }
        let center = CGPoint(x: CGFloat(b.x) * CGFloat(W), y: CGFloat(1 - b.y) * CGFloat(H))
        ctx.drawRadialGradient(grad, startCenter: center, startRadius: 0,
                               endCenter: center, endRadius: CGFloat(b.r) * CGFloat(W),
                               options: [])
    }

    guard let raw = ctx.makeImage() else { continue }

    // Flou : on étend les bords avant, sinon le flou aspire du transparent sur le pourtour.
    var img = CIImage(cgImage: raw)
    let extent = img.extent
    img = img.clampedToExtent()
        .applyingFilter("CIGaussianBlur", parameters: [kCIInputRadiusKey: 90])
        .cropped(to: extent)

    guard let out = ciContext.createCGImage(img, from: extent) else { continue }

    let url = URL(fileURLWithPath: outDir).appendingPathComponent("\(p.name).png")
    guard let dest = CGImageDestinationCreateWithURL(url as CFURL, "public.png" as CFString, 1, nil) else { continue }
    CGImageDestinationAddImage(dest, out, nil)
    if CGImageDestinationFinalize(dest) {
        print("ok  \(url.path)")
    } else {
        FileHandle.standardError.write("échec écriture \(p.name)\n".data(using: .utf8)!)
    }
}
