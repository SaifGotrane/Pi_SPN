import { ChangeDetectorRef, Component, ElementRef, ViewChild } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { AuthenticationService } from '../core/services/authentication.service';
import { Router } from '@angular/router';
import { saveAs } from 'file-saver';
import { Location } from '@angular/common';
<<<<<<< HEAD
import { PDFDocument, rgb, StandardFonts } from 'pdf-lib';

=======
import { IntroPage } from '../pages/intro/intro.page';
>>>>>>> e6e2d15a56cf59ee7a8fe60d0adee9340a2f46d7

// Import easyocr
function find_oldest_date(extracted_dates: string[]): string {
  const date_objects = extracted_dates.map(date_str => {
    const [day, month, year] = date_str.split('/');
    return new Date(parseInt(year), parseInt(month) - 1, parseInt(day)); // Months are 0-based in JavaScript Date objects
  });

  const oldest_date = new Date(Math.min(...date_objects.map(date => date.getTime()))); // Convert dates to milliseconds and then find the minimum
  const formatted_oldest_date = `${oldest_date.getDate()}/${oldest_date.getMonth() + 1}/${oldest_date.getFullYear()}`;

  return formatted_oldest_date;
}

@Component({
  selector: 'app-tab1',
  templateUrl: 'tab1.page.html',
  styleUrls: ['tab1.page.scss'],
})
export class Tab1Page {
  @ViewChild('input') input!: ElementRef<HTMLInputElement>;
  selectedFile: File | undefined;
  detectedLanguage: string | undefined;
  showLanguageSelection: boolean = false;
  selectedLanguage: string | undefined;
  submitLanguage: string | undefined;
  extractedMatricules: string[] = [];
  finalPlace: string[] = [];
  extracteddate: string;
  showMatricules: boolean = false;
  imageData: { matricules: string, place: string, date: string }[] = [];

  constructor(
    private authService: AuthenticationService,
    private router: Router,
    private http: HttpClient,
    private cdr: ChangeDetectorRef, // Inject ChangeDetectorRef
    private location: Location // Inject Location
  ) { }

  async onFileSelected(event: any) {
    // Extract the file from the event object
    const selectedFile = event.target.files[0];

    // Log the file name
    console.log('File selected:', selectedFile.name);

    // Store the selected file in the component property
    this.selectedFile = selectedFile;

    // Call the function to process the selected file
    await this.processImage();
  }

  async processImage() {
    if (!this.selectedFile) {
      console.error('No file selected');
      return;
    }

    console.log('Starting image processing...');

    const formData = new FormData();
    formData.append('image', this.selectedFile);

    try {
      console.log('Sending HTTP request...');
      const response = await this.http.post<any>('http://localhost:5000/process_image', formData).toPromise();
      console.log('HTTP response:', response);

      // Update detected language after successful response
      this.detectedLanguage = response.detected_language; // corrected property name
      console.log('Language detected:', this.detectedLanguage);

      // Show the language confirmation message
      this.showLanguageSelection = false;
    } catch (error) {
      console.error('Error processing image:', error);
      return; // Stop further execution if there's an error
    }
  }

  async logoutAndUploadImage() {
    console.log('Starting logout...');
    await this.authService.logout();
    this.router.navigateByUrl('/', { replaceUrl: true });
  }

  confirmLanguage() {
    // Implement your confirmation logic here
    console.log('Confirmed language:', this.detectedLanguage);
    // You can add further logic here, like sending confirmation to the server
  }

  selectLanguage(language: string) {
    console.log('Select language function called');
    // Vous pouvez effectuer des actions en fonction de la langue sélectionnée ici
    console.log('Langue sélectionnée:', language);
    this.selectedLanguage = language; // Met à jour la langue sélectionnée dans la propriété selectedLanguage
    this.showMatricules = true; // Afficher les données extraites
  }

  async submiterLanguage() {
    try {
      const submitLanguage = this.selectedLanguage !== undefined ? this.selectedLanguage : this.detectedLanguage;
      const requestData = {
        submitLanguage: submitLanguage
      };
      const response = await this.http.post<any>('http://localhost:5000/process_image_easyocr', requestData).toPromise();
      console.log(response);

      // Extraire les données
      const matricule = response.matricule;
      const dates = response.global_list;
      const places = response.places;

      // Afficher les données extraites dans la console
      console.log('Extracted Matricule:', matricule);
      console.log('Extracted Dates:', dates);
      console.log('Extracted Places:', places);

      // Récupérer la date la plus ancienne
      const oldestDate = find_oldest_date(dates);
      console.log('Oldest Date:', oldestDate);
      this.extracteddate = oldestDate;

      // Mise à jour des propriétés
      this.extractedMatricules = matricule;

      // Logique de sélection de la place finale
      const placesCount = {};
      places.forEach((place) => {
        const lowercasePlace = place.toLowerCase().trim(); // Trim et met en minuscule pour éviter les doublons
        placesCount[lowercasePlace] = (placesCount[lowercasePlace] || 0) + 1;
      });

      let maxOccurrence = 0;
      let finalPlace = null;

      for (const place in placesCount) {
        if (Object.prototype.hasOwnProperty.call(placesCount, place)) {
          if (placesCount[place] > maxOccurrence) {
            maxOccurrence = placesCount[place];
            finalPlace = place;
          }
        }

      }

      // Afficher la place finale
      console.log('Final Place:', finalPlace);

      // Mise à jour de la propriété finalPlace
      this.finalPlace = [finalPlace]; // Si vous avez besoin d'un tableau pour correspondre au type de finalPlace

      // Ajouter les données extraites dans le tableau imageData
      this.imageData.push({ matricules: matricule, place: finalPlace, date: oldestDate });

      // Mise à jour des autres propriétés et déclenchement de la détection de changement
      this.detectedLanguage = undefined;
      this.showLanguageSelection = false;
      this.selectedFile = undefined;
      this.showMatricules = true;
      this.cdr.detectChanges();

      // Appeler la fonction pour soumettre les données extraites
      await this.submitExtractedData(matricule, oldestDate, finalPlace);

    } catch (error) {
      // Gérer les erreurs
      console.error('Error:', error);
    }
  }

  async submitExtractedData(matricule: string, extractedDate: string, finalPlace: string) {
    try {
      const requestData = {
        extractedmatricule: matricule,
        extracteddate: extractedDate,
        finalPlace: finalPlace
      };
      const response = await this.http.post<any>('http://localhost:5000/submit_data', requestData).toPromise();
      console.log(response);

      // Gérer la réponse ici si nécessaire

    } catch (error) {
      console.error('Error:', error);
    }
  }

  selectLanguageAndSubmit(language: string) {
    this.selectLanguage(language); // Appel de la fonction selectLanguage
    this.submiterLanguage(); // Appel de la fonction submiterLanguage
  }

  confirmResults() {
    console.log('Confirming results and saving to CSV...');

    // Obtenir la matricule, la date la plus ancienne et la place finale
    const matricule = this.extractedMatricules[0]; // Supposons que vous voulez soumettre la première matricule extraite
    const oldestDate = this.extracteddate;
    const finalPlace = this.finalPlace[0]; // Supposons que vous voulez soumettre la première place extraite

    // Appeler la fonction pour soumettre les données extraites
    this.submitExtractedData(matricule, oldestDate, finalPlace);

    //pdf 
    this.generatePDF(matricule, oldestDate, finalPlace);
  }
  
  async generatePDF(matricule: string, extractedDate: string, finalPlace: string) {
    // Créer un nouveau document PDF
    const pdfDoc = await PDFDocument.create();
    
    // Ajouter une nouvelle page au document PDF
    const page = pdfDoc.addPage();
    
    // Définir la taille de la page (A4)
    page.setSize(595, 842); // Largeur: 595 points, Hauteur: 842 points
    
    // Construire le message personnalisé avec les données extraites
    const message = `SPN\nHello sir/madam, you have a penalty since the date ${extractedDate} when renting our car with registration\n number ${matricule} in ${finalPlace}`;
    
    // Ajouter le contenu du message à la page PDF
    page.drawText(message, {
      x: 50,
      y: page.getHeight() - 100,
      size: 12,
      font: await pdfDoc.embedFont(StandardFonts.Helvetica),
      color: rgb(0, 0, 0),
    });
    
    // Enregistrer le document PDF dans un fichier
    const pdfBytes = await pdfDoc.save();
    
    // Télécharger le fichier PDF
    const blob = new Blob([pdfBytes], { type: 'application/pdf' });
    saveAs(blob, 'formulaire.pdf');
  }
  
  goBack() {
    window.location.href = 'http://localhost:4200/intro';  }
}
